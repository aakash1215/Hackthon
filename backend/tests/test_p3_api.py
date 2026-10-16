"""P3 over HTTP (models stubbed): consented thekedar/co-worker recordings, hisaab differences,
corroboration levels in the ledger, payment proof and site-board photos, evidence packet."""
import hashlib
import io
import json
import zipfile

import pytest

from app import db, events, extract, packet
from tests.test_entries_api import _null, _save, client, stub_models  # noqa: F401  (fixture import)

PHOTO = b"\xff\xd8\xff\xe0fake-jpeg-bytes" * 20
SITE_PT = (18.5204, 73.8567)


def _sha(b):
    return hashlib.sha256(b).hexdigest()


def _setup(wid="w1"):
    r = client.post("/api/workers", json={"id": wid, "display_name": "Sunita", "language": "mr",
                                           "category": "unskilled", "default_break_min": 60, "gps_opt_in": True})
    assert r.status_code == 200
    r = client.post("/api/sites", json={"worker_id": wid, "name": "Demo site", "state": "Maharashtra", "sphere": "state",
                                         "zone": "I", "zone_confirmed": True, "employment_sn": 11,
                                         "site_lat": SITE_PT[0], "site_lon": SITE_PT[1], "site_gps_accuracy_m": 10})
    assert r.json()["site_gps_saved"] is True
    client.post("/api/parties", json={"worker_id": wid, "role": "contractor", "name": "Kailas", "phone": "9000000000"})
    return wid


def _day(d, wid="w1", **form):
    eid = _save("workday", wid=wid, client_ts=f"{d}T20:00:00+05:30", **form).json()["entry_id"]
    assert client.post(f"/api/entries/{eid}/process").json()["status"] == "processed"
    r = client.post(f"/api/entries/{eid}/confirm", json={"fields": {
        "work_date": d, "start_time": "09:00", "end_time": "19:00", "break_minutes": 60, "worked": "yes"}})
    assert r.status_code == 200, r.text
    return eid


def _types():
    with db.read() as c:
        return [r["type"] for r in c.execute("SELECT type FROM events ORDER BY seq")]


@pytest.fixture
def three_days(stub_models):
    stub_models["llm"] = None
    _setup()
    for d in ("2026-10-01", "2026-10-02", "2026-10-03"):
        _day(d)
    return stub_models


def test_thekedar_recording_requires_notice(three_days):
    assert _save("hisaab_statement", speaker="thekedar").json()["detail"] == "NOTICE_REQUIRED"
    assert _save("workday", speaker="thekedar", notice_played="true").json()["detail"] == "BAD_KIND_FOR_SPEAKER"
    assert _save("coworker_confirm").json()["detail"] == "BAD_KIND_FOR_SPEAKER"  # the worker can't be the witness
    r = _save("hisaab_statement", speaker="thekedar", notice_played="true", notice_lang="hi")
    assert r.status_code == 200
    e = client.get(f"/api/entries/{r.json()['entry_id']}").json()
    assert e["notice_played"] == 1 and e["language"] == "auto"
    assert "THEKEDAR_RECORDED" in _types()


def test_thekedar_recording_to_differences_and_dispute_flag(three_days, monkeypatch):
    s = three_days
    s["text"] = "2 दिन, 600 रोज़, 2000 उचल काटी"
    s["llm"] = _null("hisaab_statement", {
        "days_counted": {"value": 2, "evidence": "2 दिन"},
        "rate_per_day": {"value": 6000, "evidence": "600 रोज़"},  # the LLM misreads; code reads the quote
        "deductions": {"value": 2000, "evidence": "2000 उचल काटी"},
        "paid_now": {"value": 500, "evidence": "invented"},  # not in the transcript → dropped
    })
    monkeypatch.setattr(extract, "extract_reply", lambda t, timeout=300: {
        "intent": "disputes_days", "confidence": "high", "amount": {"value": None, "evidence": None},
        "date": {"value": None, "evidence": None}, "days": {"value": 2, "evidence": "2 दिन"}})
    eid = _save("hisaab_statement", speaker="thekedar", notice_played="true", notice_lang="hi",
                client_ts="2026-10-04T18:00:00+05:30").json()["entry_id"]
    p = client.post(f"/api/entries/{eid}/process").json()
    f = p["fields"]
    assert f["days_counted"]["status"] == "green" and f["days_counted"]["value"] == 2
    assert f["rate_per_day"]["status"] == "amber" and f["rate_per_day"]["candidates"] == [600, 6000]
    assert f["deductions"]["value"] == 2000
    assert f["paid_now"]["value"] is None and "UNGROUNDED" in f["paid_now"]["flags"]
    assert p["reply"]["intent"] == "disputes_days" and p["reply"]["days"]["value"] == 2

    assert client.get(f"/api/entries/{eid}/differences").status_code == 409  # only after the worker confirms
    r = client.post(f"/api/entries/{eid}/confirm", json={"fields": {
        "days_counted": 2, "rate_per_day": 600, "deductions": 2000, "intent": "disputes_days"}})
    assert r.status_code == 200, r.text
    d = client.get(f"/api/entries/{eid}/differences").json()
    assert [i["code"] for i in d["items"]] == ["DAYS_DIFF", "RATE_BELOW_MIN", "OT_NOT_COUNTED", "DEDUCTION_DISPUTED"]
    assert d["thekedar_total"] == "-800.00"  # 2 x 600 - 2000, computed by code from confirmed values
    assert d["items"][0]["thekedar"] == "2" and d["items"][0]["record"] == "3"
    assert d["record_total"] is not None and d["window"] == ["2026-10-01", "2026-10-04"]

    led = client.get("/api/ledger", params={"worker_id": "w1"}).json()
    for day in led["days"]:
        assert day["corroboration"]["flags"] == ["THEKEDAR_DISPUTES"]
    assert client.get("/api/statements", params={"worker_id": "w1"}).json()["items"][0]["count"] == 4


def test_thekedar_promise_logs_promise(three_days, monkeypatch):
    monkeypatch.setattr(extract, "extract_reply", lambda t, timeout=300: {"intent": "promise_to_pay"})
    three_days["text"] = "सोमवार को 5000 दूँगा"
    eid = _save("hisaab_statement", speaker="thekedar", notice_played="true",
                client_ts="2026-10-04T18:00:00+05:30").json()["entry_id"]
    client.post(f"/api/entries/{eid}/process")
    r = client.post(f"/api/entries/{eid}/confirm", json={"fields": {
        "days_counted": 3, "balance_promised": 5000, "promised_date": "सोमवार", "intent": "promise_to_pay"}})
    assert r.status_code == 200
    assert "PROMISE_LOGGED" in _types()
    led = client.get("/api/ledger", params={"worker_id": "w1"}).json()
    assert all(d["corroboration"]["level"] == 3 for d in led["days"])  # 3 of 3 days acknowledged
    assert client.post(f"/api/entries/{eid}/confirm", json={"fields": {"intent": "bribe"}}).status_code == 409


def test_coworker_confirmation_raises_day_to_l3(three_days):
    assert _save("coworker_confirm", speaker="coworker").json()["detail"] == "NOTICE_REQUIRED"
    three_days["text"] = "मेरा नाम रमेश है, राज़ी हूँ"
    eid = _save("coworker_confirm", speaker="coworker", notice_played="true").json()["entry_id"]
    client.post(f"/api/entries/{eid}/process")
    no = client.post(f"/api/entries/{eid}/confirm", json={"fields": {"coworker_name": "रमेश", "dates": ["2026-10-01"]}})
    assert no.json()["detail"] == "CONSENT_REQUIRED"
    r = client.post(f"/api/entries/{eid}/confirm", json={"fields": {
        "coworker_name": "रमेश", "consent": True, "dates": ["2026-10-01", "2026-10-02"]}})
    assert r.status_code == 200, r.text
    led = {d["date"]: d for d in client.get("/api/ledger", params={"worker_id": "w1"}).json()["days"]}
    assert led["2026-10-01"]["corroboration"]["level"] == 3
    assert "COWORKER" in led["2026-10-02"]["corroboration"]["signals"]
    assert led["2026-10-03"]["corroboration"]["level"] == 1
    with db.read() as c:
        payloads = [r["payload_json"] for r in c.execute("SELECT payload_json FROM events")]
    assert not any("रमेश" in p for p in payloads)  # the witness name stays out of the chain
    assert "COWORKER_CONFIRMED" in _types()


def test_gps_and_photo_on_the_day_give_l2(stub_models):
    stub_models["llm"] = None
    _setup()
    _day("2026-10-01", lat=str(SITE_PT[0] + 0.001), lon=str(SITE_PT[1]), gps_accuracy_m="15",
         gps_ts="2026-10-01T19:00:00+05:30")
    _day("2026-10-02")
    _day("2026-10-03")
    r = client.post("/api/evidence/photo", files={"photo": ("p.jpg", PHOTO, "image/jpeg")},
                    data={"worker_id": "w1", "kind": "photo", "client_ts": "2026-10-02T11:00:00+05:30",
                          "client_sha256": _sha(PHOTO)})
    assert r.json()["hash_match"] is True and r.json()["sha256"] == _sha(PHOTO)
    led = {d["date"]: d for d in client.get("/api/ledger", params={"worker_id": "w1"}).json()["days"]}
    assert led["2026-10-01"]["corroboration"]["signals"] == ["SELF", "GPS_AT_SITE"]
    assert led["2026-10-02"]["corroboration"]["signals"] == ["SELF", "PHOTO"]
    assert led["2026-10-03"]["corroboration"]["level"] == 1


def test_payment_proof_photo_and_site_board(three_days):
    r = client.post(
        "/api/entries", files={"audio": ("n.webm", b"pay" * 99, "audio/webm"), "photo": ("slip.jpg", PHOTO, "image/jpeg")},
        data={"kind": "payment", "worker_id": "w1", "photo_client_sha256": _sha(PHOTO),
              "client_ts": "2026-10-03T20:00:00+05:30"})
    pid = r.json()["entry_id"]
    client.post(f"/api/entries/{pid}/process")
    client.post(f"/api/entries/{pid}/confirm", json={"fields": {"payment_date": "2026-10-03", "amount_paid": 1500}})
    ev = client.get("/api/evidence", params={"worker_id": "w1", "kind": "payment_proof"}).json()["items"]
    assert len(ev) == 1 and ev[0]["sha256"] == _sha(PHOTO) and ev[0]["hash_match"] == 1
    led = client.get("/api/ledger", params={"worker_id": "w1"}).json()
    assert led["payments"][0]["proof_photos"] == 1
    # a second proof attached later
    r2 = client.post("/api/evidence/photo", files={"photo": ("s2.jpg", PHOTO + b"2", "image/jpeg")},
                     data={"worker_id": "w1", "kind": "payment_proof", "entry_id": pid})
    assert r2.status_code == 200
    day_eid = led["days"][0]["entry_id"]
    bad = client.post("/api/evidence/photo", files={"photo": ("s.jpg", PHOTO, "image/jpeg")},
                      data={"worker_id": "w1", "kind": "payment_proof", "entry_id": day_eid})
    assert bad.json()["detail"] == "NOT_A_PAYMENT"
    b = client.post("/api/sites/board", json={"worker_id": "w1", "principal_employer": "Example Developers",
                                               "maharera_no": "P52100000000"})
    assert b.json()["maharera_no"] == "P52100000000"
    coach = client.get("/api/coach", params={"worker_id": "w1"}).json()
    assert coach["total"] == 12 and {i["id"]: i["ok"] for i in coach["items"]}["site_board"] is True


def test_deleted_entry_is_not_reprocessed(three_days):
    eid = _save("workday").json()["entry_id"]
    client.delete(f"/api/entries/{eid}")
    assert client.post(f"/api/entries/{eid}/process").json()["detail"] == "DELETED"


def test_manual_statement_typed(three_days):
    r = client.post("/api/entries/manual", json={"worker_id": "w1", "client_ts": "2026-10-04T10:00:00+05:30"})
    eid = r.json()["entry_id"]
    c = client.post(f"/api/entries/{eid}/confirm", json={"fields": {"days_counted": 3, "rate_per_day": 900}})
    assert c.status_code == 200
    d = client.get(f"/api/entries/{eid}/differences").json()
    assert "DAYS_DIFF" not in [i["code"] for i in d["items"]]


def test_packet_bundle_manifest_and_redaction(three_days, monkeypatch):
    monkeypatch.setattr(packet, "_render_pdf", lambda html, pdf: "PDF_UNAVAILABLE:test")
    three_days["text"] = "मेरा नाम रमेश है"
    eid = _save("coworker_confirm", speaker="coworker", notice_played="true", audio=b"witness" * 50).json()["entry_id"]
    client.post(f"/api/entries/{eid}/process")
    client.post(f"/api/entries/{eid}/confirm", json={"fields": {"coworker_name": "रमेश", "consent": True,
                                                                "dates": ["2026-10-01"]}})
    out = client.post("/api/export", json={"worker_id": "w1", "date_from": "2026-10-01", "date_to": "2026-10-31"}).json()
    assert out["pdf_url"] is None and out["errors"] == ["PDF_UNAVAILABLE:test"]
    html = client.get(out["html_url"]).text
    assert "SYNTHETIC DEMO DATA" in html and "रमेश" not in html and "L3" in html
    assert "@font-face" in html and "Noto Sans Devanagari" in html
    z = zipfile.ZipFile(io.BytesIO(client.get(out["zip_url"]).content))
    manifest = json.loads(z.read("manifest.json"))
    assert _sha(z.read("manifest.json")) == out["manifest_sha256"]
    for f in manifest["files"]:
        assert _sha(z.read(f["path"])) == f["sha256"]
    assert not any("coworker" in f["path"] for f in manifest["files"])  # witness audio not shared by default
    assert sum(1 for f in manifest["files"] if f["kind"] == "audio:workday") == 3
    assert "EXPORT_CREATED" in _types()
    with db.read() as c:
        assert events.verify(c)["ok"]


def test_packet_pdf_renders_with_chromium(three_days):
    out = client.post("/api/export", json={"worker_id": "w1"}).json()
    if out["pdf_url"] is None:
        pytest.skip(f"Chromium not available here: {out['errors']}")
    pdf = client.get(out["pdf_url"]).content
    assert pdf[:4] == b"%PDF" and b"NotoSansDevanagari" in pdf.replace(b"-", b"").replace(b" ", b"")


def test_thekedar_refusal_keeps_only_the_notice_and_is_never_processed(three_days):
    r = _save("hisaab_statement", speaker="thekedar", notice_played="true", consent_refused="true",
              audio=b"notice-only" * 30)
    eid = r.json()["entry_id"]
    assert client.post(f"/api/entries/{eid}/process").json()["detail"] == "CONSENT_REFUSED"
    with db.read() as c:
        ev = c.execute("SELECT payload_json FROM events WHERE type='THEKEDAR_RECORDED'").fetchone()
    assert json.loads(ev["payload_json"])["consent_refused"] is True
    assert _save("coworker_confirm", speaker="coworker", notice_played="true",
                 consent_refused="true").json()["detail"] == "BAD_SPEAKER"
