"""End-to-end over HTTP with ASR and the LLM stubbed (models are not needed for CI).

Covers: save+hash first, hash mismatch flagged, process → reconcile, LLM/ASR down degrade,
confirm → events, ledger, hisaab (engine wrapper), GPS opt-in, chain verify.
"""
import hashlib
import shutil

import pytest
from fastapi.testclient import TestClient

from app import asr, extract, events, db
from app.contracts import KIND_FIELDS
from app.main import app

client = TestClient(app)

MR_WORKDAY = "सकाळी नऊ वाजता कामावर गेलो आणि संध्याकाळी सहा वाजता सुटलो."
MR_PAYMENT = "ठेकेदार ने आज पाँच सौ रुपये दिए"
AUDIO = b"not-really-webm-but-bytes-are-bytes" * 50


def _sha(b):
    return hashlib.sha256(b).hexdigest()


def _null(kind, partial):
    out = {n: {"value": None, "evidence": None} for n in KIND_FIELDS[kind]}
    out.update(partial)
    return out


@pytest.fixture
def stub_models(monkeypatch):
    """Replace ffmpeg + ASR + LLM. Each test sets what the 'models' return."""
    state = {"text": MR_WORKDAY, "llm": None, "llm_error": None, "asr_error": None}

    def fake_wav(src, dst):
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        return dst

    def fake_asr(wav, language):
        if state["asr_error"]:
            raise asr.ASRUnavailable(state["asr_error"])
        return {"language": language if language != "auto" else "mr", "duration": 7.4, "text": state["text"],
                "segments": [{"start": 0, "end": 7.4, "text": state["text"],
                              "avg_logprob": -0.3, "no_speech_prob": 0.01, "words": []}]}

    def fake_extract(kind, transcript, rec_date, context=None, timeout=300):
        if state["llm_error"]:
            raise extract.LLMUnavailable(state["llm_error"])
        return state["llm"]

    monkeypatch.setattr(asr, "to_wav16k", fake_wav)
    monkeypatch.setattr(asr, "transcribe_wav", fake_asr)
    monkeypatch.setattr(extract, "extract", fake_extract)
    return state


def _worker(wid="w1", gps=False, break_min=60):
    r = client.post("/api/workers", json={"id": wid, "language": "mr", "category": "unskilled",
                                           "default_break_min": break_min, "gps_opt_in": gps})
    assert r.status_code == 200, r.text
    return wid


def _site(wid="w1"):
    r = client.post("/api/sites", json={"worker_id": wid, "name": "Demo site", "state": "Maharashtra",
                                         "sphere": "state", "zone": "I", "zone_confirmed": True,
                                         "employment_sn": 11, "wage_period": "unknown"})
    assert r.status_code == 200, r.text


def _save(kind, wid="w1", audio=AUDIO, **form):
    data = {"kind": kind, "worker_id": wid, **form}
    return client.post("/api/entries", files={"audio": ("note.webm", audio, "audio/webm")}, data=data)


def test_save_hashes_original_bytes_before_anything_else(stub_models):
    _worker()
    r = _save("workday", client_sha256=_sha(AUDIO))
    body = r.json()
    assert r.status_code == 200
    assert body["status"] == "saved"
    assert body["audio_sha256"] == _sha(AUDIO)
    assert body["hash_match"] is True
    e = client.get(f"/api/entries/{body['entry_id']}").json()
    assert e["audio_sha256"] == _sha(AUDIO)
    assert e["status"] == "saved"


def test_client_hash_mismatch_is_flagged_never_fixed(stub_models):
    _worker()
    r = _save("workday", client_sha256="0" * 64)
    assert r.json()["hash_match"] is False
    assert r.json()["audio_sha256"] == _sha(AUDIO)  # the server keeps the real hash
    with db.read() as c:
        types = [row["type"] for row in c.execute("SELECT type FROM events ORDER BY seq")]
    assert "HASH_MISMATCH" in types


def test_gps_dropped_unless_worker_opted_in(stub_models):
    _worker("w_no", gps=False)
    r = _save("workday", wid="w_no", lat="12.97", lon="77.59")
    assert r.json()["gps_saved"] is False and r.json()["gps_dropped"] is True
    _worker("w_yes", gps=True)
    r2 = _save("workday", wid="w_yes", lat="18.52", lon="73.85", gps_accuracy_m="12")
    assert r2.json()["gps_saved"] is True
    e = client.get(f"/api/entries/{r2.json()['entry_id']}").json()
    assert round(e["lat"], 2) == 18.52


def test_bad_kind_and_unknown_worker(stub_models):
    assert _save("witness").status_code == 422
    assert _save("workday", wid="nobody").status_code == 404


def test_process_then_confirm_then_ledger_and_hisaab(stub_models):
    _worker(break_min=60)
    _site()
    stub_models["text"] = MR_WORKDAY
    stub_models["llm"] = _null("workday", {
        "start_time": {"value": "9:00 AM", "evidence": "सकाळी नऊ वाजता"},
        "end_time": {"value": "6:00 PM", "evidence": "संध्याकाळी सहा वाजता"},
        "worked": {"value": "yes", "evidence": "कामावर गेलो"},
    })
    eid = _save("workday", client_ts="2026-10-16T10:00:00+05:30").json()["entry_id"]

    p = client.post(f"/api/entries/{eid}/process").json()
    assert p["status"] == "processed", p
    f = p["fields"]
    assert f["start_time"]["status"] == "green" and f["start_time"]["value"] == "09:00"
    assert f["end_time"]["status"] == "green" and f["end_time"]["value"] == "18:00"
    assert f["break_minutes"]["value"] == 60 and f["break_minutes"]["status"] == "amber"  # default, to confirm
    assert f["start_time"]["candidates"] == ["09:00"]

    cf = client.post(f"/api/entries/{eid}/confirm", json={"fields": {
        "work_date": "2026-10-16", "start_time": "09:00", "end_time": "18:00",
        "break_minutes": 60, "worked": "yes"}})
    assert cf.status_code == 200, cf.text
    assert cf.json()["status"] == "confirmed"
    assert cf.json()["chain_head"]["short"]

    led = client.get("/api/ledger", params={"worker_id": "w1"}).json()
    assert len(led["days"]) == 1 and led["days"][0]["start_time"] == "09:00"

    pid = _save("payment", client_ts="2026-10-16T19:00:00+05:30").json()["entry_id"]
    stub_models["text"] = MR_PAYMENT
    stub_models["llm"] = _null("payment", {"amount_paid": {"value": "500", "evidence": "पाँच सौ रुपये"}})
    pp = client.post(f"/api/entries/{pid}/process").json()
    assert pp["fields"]["amount_paid"]["status"] == "green"
    client.post(f"/api/entries/{pid}/confirm", json={"fields": {"payment_date": "2026-10-16", "amount_paid": 500}})

    h = client.get("/api/hisaab", params={"worker_id": "w1"}).json()
    # F1-style: 8 h day, daily minimum 863.96, paid 500 → statutory shortfall 363.96
    assert h["ok"] is True, h
    assert "363.96" in str(h)

    chain = client.get("/api/chain/verify").json()
    assert chain["ok"] is True and chain["events"] > 5


def test_confirm_rejects_unknown_or_bad_fields(stub_models):
    _worker()
    _site()
    stub_models["llm"] = _null("workday", {"start_time": {"value": "9:00 AM", "evidence": "सकाळी नऊ वाजता"}})
    stub_models["text"] = MR_WORKDAY
    eid = _save("workday").json()["entry_id"]
    client.post(f"/api/entries/{eid}/process")
    assert client.post(f"/api/entries/{eid}/confirm", json={"fields": {"salary": 5}}).status_code == 422
    assert client.post(f"/api/entries/{eid}/confirm", json={"fields": {"start_time": "25:00"}}).status_code == 422
    assert client.post(f"/api/entries/{eid}/confirm", json={"fields": {"start_time": "09:00"}}).status_code == 200
    assert client.post(f"/api/entries/{eid}/confirm", json={"fields": {"start_time": "09:00"}}).status_code == 409


def test_llm_down_keeps_entry_saved_with_reader_one_candidates(stub_models):
    _worker()
    stub_models["text"] = MR_WORKDAY
    stub_models["llm_error"] = "LLM_ConnectTimeout"
    eid = _save("workday").json()["entry_id"]
    p = client.post(f"/api/entries/{eid}/process").json()
    assert p["error"] == "LLM_ConnectTimeout"
    assert p["status"] == "saved"
    assert p["fields"]["start_time"]["status"] == "amber"  # normalizer reading only
    assert client.post(f"/api/entries/{eid}/confirm", json={"fields": {}}).status_code == 409


def test_asr_down_keeps_entry_saved_and_returns_code(stub_models):
    _worker()
    stub_models["asr_error"] = "ASR_MODEL_LOAD_FAILED: no model"
    eid = _save("workday").json()["entry_id"]
    p = client.post(f"/api/entries/{eid}/process").json()
    assert p["error"] == "ASR_MODEL_LOAD_FAILED"
    assert p["status"] == "saved"
    assert client.get(f"/api/entries/{eid}").json()["status"] == "saved"


def test_hisaab_without_site_returns_code_not_amount(stub_models):
    _worker("nosite")
    h = client.get("/api/hisaab", params={"worker_id": "nosite"}).json()
    assert h == {"ok": False, "errors": ["SITE_NOT_SET"], "days": [], "totals": None}


def test_photo_is_hashed_and_recorded(stub_models):
    _worker()
    photo = b"\xff\xd8fake-jpeg" * 20
    r = client.post("/api/entries",
                    files={"audio": ("a.webm", AUDIO, "audio/webm"), "photo": ("p.jpg", photo, "image/jpeg")},
                    data={"kind": "workday", "worker_id": "w1"})
    assert r.json()["photo_sha256"] == _sha(photo)
    with db.read() as c:
        types = [row["type"] for row in c.execute("SELECT type FROM events ORDER BY seq")]
    assert "PHOTO_SAVED" in types


def test_copy_yesterday_creates_amber_entry_without_audio(stub_models):
    _worker()
    _site()
    assert client.post("/api/entries/copy-yesterday", data={"worker_id": "w1", "client_ts": "2026-10-16T09:00:00+05:30"}).status_code == 404
    stub_models["text"] = MR_WORKDAY
    stub_models["llm"] = _null("workday", {"start_time": {"value": "9:00 AM", "evidence": "सकाळी नऊ वाजता"}})
    eid = _save("workday", client_ts="2026-10-15T20:00:00+05:30").json()["entry_id"]
    client.post(f"/api/entries/{eid}/process")
    client.post(f"/api/entries/{eid}/confirm", json={"fields": {"work_date": "2026-10-15", "start_time": "09:00",
                                                                  "end_time": "18:00", "break_minutes": 60, "worked": "yes"}})
    r = client.post("/api/entries/copy-yesterday", data={"worker_id": "w1", "client_ts": "2026-10-16T09:00:00+05:30"})
    assert r.status_code == 200, r.text
    f = r.json()["fields"]
    assert f["work_date"]["value"] == "2026-10-16" and f["start_time"]["value"] == "09:00"
    assert all(x["status"] in ("amber", "none") for x in f.values())  # nothing is pre-confirmed
    new_id = r.json()["entry_id"]
    assert client.post(f"/api/entries/{new_id}/process").status_code == 409  # no audio to process
    ok = client.post(f"/api/entries/{new_id}/confirm", json={"fields": {"work_date": "2026-10-16", "start_time": "09:00",
                                                                       "end_time": "18:00", "break_minutes": 60, "worked": "yes"}})
    assert ok.status_code == 200
    assert len(client.get("/api/ledger", params={"worker_id": "w1"}).json()["days"]) == 2


def test_empty_transcript_skips_llm(stub_models):
    _worker()
    stub_models["text"] = ""
    stub_models["llm_error"] = "SHOULD_NOT_BE_CALLED"
    eid = _save("workday").json()["entry_id"]
    p = client.post(f"/api/entries/{eid}/process").json()
    assert p["status"] == "processed" and p["error"] is None
