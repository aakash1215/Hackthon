"""P1 HTTP API: save+hash entries, process (ASR → normalize → extract → reconcile), confirm,
ledger, hisaab, worker/site/party profiles and chain verify.

Order is fixed: the original bytes are hashed and saved before any model call. Model calls
run outside the DB write lock. A model being down leaves the entry `saved`, never an error.
"""
from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel

from . import asr, corroboration, db, events, extract, normalize, processing, reconcile
from .config import settings
from .contracts import (
    DATE_FIELDS, ENTRY_KINDS, ENUM_FIELDS, INT_FIELDS, KIND_FIELDS, MONEY_FIELDS, REPLY_INTENTS, SPAN_INT_FIELDS,
    SPAN_MONEY_FIELDS, TIME_FIELDS,
)
from .rates import RateContext, load_packs
from .wage_engine import Payment, WorkDay, compute, parse_time

router = APIRouter()
KINDS = ENTRY_KINDS
# Who may speak on which kind of recording. Anyone but the worker needs the notice / consent prompt first.
SPEAKER_KIND = {"thekedar": "hisaab_statement", "coworker": "coworker_confirm"}
JSON_COLS = ("asr_meta", "extraction", "reconciled", "confirmed", "linked_day_ids", "reply")
_TIME_RE = re.compile(r"^\d{2}:\d{2}$")


# --- helpers -----------------------------------------------------------------

def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _ext(filename: str | None, default: str) -> str:
    suffix = Path(filename or "").suffix.lower()
    return suffix if re.fullmatch(r"\.[a-z0-9]{1,6}", suffix or "") else default


def _row(conn, table: str, row_id: str) -> dict | None:
    r = conn.execute(f"SELECT * FROM {table} WHERE id = ?", (row_id,)).fetchone()
    return _decode(dict(r)) if r else None


def _decode(d: dict) -> dict:
    for c in JSON_COLS:
        if d.get(c):
            d[c] = json.loads(d[c])
    return d


def _rec_date(entry: dict) -> date:
    for ts in (entry.get("client_ts"), entry.get("server_ts")):
        if ts:
            try:
                return date.fromisoformat(ts[:10])
            except ValueError:
                continue
    return date.today()


def _site_for(conn, worker_id: str) -> dict | None:
    r = conn.execute("SELECT * FROM sites WHERE worker_id = ? ORDER BY created_at LIMIT 1", (worker_id,)).fetchone()
    return dict(r) if r else None


def _coerce(kind: str, name: str, v: Any):
    """Validate a worker-confirmed value. Confirmed values are the only ones that reach the engine."""
    if v in (None, ""):
        return None
    if name not in KIND_FIELDS[kind]:
        raise HTTPException(422, f"UNKNOWN_FIELD:{name}")
    if name in TIME_FIELDS:
        if not isinstance(v, str) or not _TIME_RE.match(v):
            raise HTTPException(422, f"BAD_TIME:{name}")
        h, m = (int(x) for x in v.split(":"))
        if h > 23 or m > 59:
            raise HTTPException(422, f"BAD_TIME:{name}")
        return v
    if name in DATE_FIELDS:
        try:
            return date.fromisoformat(str(v)).isoformat()
        except ValueError as e:
            raise HTTPException(422, f"BAD_DATE:{name}") from e
    if name in MONEY_FIELDS:
        try:
            n = int(v)
        except (TypeError, ValueError) as e:
            raise HTTPException(422, f"BAD_AMOUNT:{name}") from e
        if n < 0:
            raise HTTPException(422, f"BAD_AMOUNT:{name}")
        return n
    if name in SPAN_MONEY_FIELDS or name in SPAN_INT_FIELDS:
        try:
            n = int(v)
        except (TypeError, ValueError) as e:
            raise HTTPException(422, f"BAD_NUMBER:{name}") from e
        if not 0 <= n <= (366 if name in SPAN_INT_FIELDS else 10_000_000):
            raise HTTPException(422, f"BAD_NUMBER:{name}")
        return n
    if name in INT_FIELDS:
        try:
            n = int(v)
        except (TypeError, ValueError) as e:
            raise HTTPException(422, f"BAD_INT:{name}") from e
        if not 0 <= n <= 600:
            raise HTTPException(422, f"BAD_INT:{name}")
        return n
    if name in ENUM_FIELDS and str(v) not in ENUM_FIELDS[name]:
        raise HTTPException(422, f"BAD_ENUM:{name}")
    return str(v)[:500]


# --- workers, sites, parties (profile) ---------------------------------------

class WorkerIn(BaseModel):
    id: str | None = None
    display_name: str | None = None
    language: Literal["hi", "mr"] = "mr"
    category: Literal["unskilled", "semi_skilled", "skilled", "highly_skilled"] | None = None
    default_break_min: int | None = None
    consent_keep_audio: bool = False
    gps_opt_in: bool = False


@router.post("/api/workers")
def upsert_worker(body: WorkerIn):
    wid = body.id or uuid.uuid4().hex[:12]
    with db.write() as c:
        c.execute(
            "INSERT INTO workers (id, display_name, language, category, default_break_min, consent_keep_audio, "
            "gps_opt_in, created_at) VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET "
            "display_name=excluded.display_name, language=excluded.language, category=excluded.category, "
            "default_break_min=excluded.default_break_min, consent_keep_audio=excluded.consent_keep_audio, "
            "gps_opt_in=excluded.gps_opt_in",
            (wid, body.display_name, body.language, body.category, body.default_break_min,
             int(body.consent_keep_audio), int(body.gps_opt_in), _now()),
        )
        events.append(c, "WORKER_SET", {"worker_id": wid, "language": body.language,
                                         "category": body.category, "gps_opt_in": body.gps_opt_in}, wid)
    return {"id": wid, "gps_opt_in": body.gps_opt_in}


@router.get("/api/workers/{worker_id}")
def get_worker(worker_id: str):
    with db.read() as c:
        w = _row(c, "workers", worker_id)
        if not w:
            raise HTTPException(404, "WORKER_NOT_FOUND")
        site = _site_for(c, worker_id)
        parties = [dict(p) for p in c.execute("SELECT * FROM parties WHERE worker_id = ?", (worker_id,))]
    return {"worker": w, "site": site, "parties": parties}


class SiteIn(BaseModel):
    worker_id: str
    name: str | None = None
    landmark: str | None = None
    city: str | None = None
    state: str | None = "Maharashtra"
    sphere: Literal["state", "central", "unknown"] = "state"
    zone: Literal["I", "II", "III", "A", "B", "C"] | None = None
    zone_confirmed: bool = False
    principal_employer: str | None = None
    maharera_no: str | None = None
    employment_sn: int | None = 11
    wage_period: Literal["daily", "weekly", "fortnightly", "monthly", "unknown"] = "unknown"
    site_lat: float | None = None
    site_lon: float | None = None
    site_gps_accuracy_m: float | None = None


@router.post("/api/sites")
def upsert_site(body: SiteIn):
    """One site per worker in P1. The site GPS point is set from the first fix only (opt-in workers)."""
    with db.write() as c:
        w = _row(c, "workers", body.worker_id)
        if not w:
            raise HTTPException(404, "WORKER_NOT_FOUND")
        existing = _site_for(c, body.worker_id)
        sid = existing["id"] if existing else uuid.uuid4().hex[:12]
        gps_ok = bool(w["gps_opt_in"]) and body.site_lat is not None and body.site_lon is not None
        keep_gps = existing and existing["site_lat"] is not None
        lat = lon = acc = None
        if gps_ok and not keep_gps:
            lat, lon, acc = body.site_lat, body.site_lon, body.site_gps_accuracy_m
        elif existing:
            lat, lon, acc = existing["site_lat"], existing["site_lon"], existing["site_gps_accuracy_m"]
        vals = (body.name, body.landmark, body.city, body.state, body.sphere, body.zone,
                int(body.zone_confirmed), body.principal_employer, body.maharera_no,
                body.employment_sn, body.wage_period, lat, lon, acc)
        if existing:
            c.execute(
                "UPDATE sites SET name=?, landmark=?, city=?, state=?, sphere=?, zone=?, zone_confirmed=?, "
                "principal_employer=?, maharera_no=?, employment_sn=?, wage_period=?, site_lat=?, site_lon=?, "
                "site_gps_accuracy_m=? WHERE id=?", (*vals, sid))
        else:
            c.execute(
                "INSERT INTO sites (id, worker_id, name, landmark, city, state, sphere, zone, zone_confirmed, "
                "principal_employer, maharera_no, employment_sn, wage_period, site_lat, site_lon, "
                "site_gps_accuracy_m, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (sid, body.worker_id, *vals, _now()))
        events.append(c, "SITE_SET", {"site_id": sid, "sphere": body.sphere, "zone": body.zone,
                                       "zone_confirmed": body.zone_confirmed}, body.worker_id)
        if lat is not None and not keep_gps:
            events.append(c, "GPS_CAPTURED", {"site_id": sid, "lat": lat, "lon": lon, "accuracy_m": acc},
                          body.worker_id)
    return {"id": sid, "site_gps_saved": lat is not None, "gps_dropped": body.site_lat is not None and not gps_ok}


class PartyIn(BaseModel):
    worker_id: str
    site_id: str | None = None
    role: Literal["mukadam", "contractor", "subcontractor", "principal_employer"]
    name: str | None = None
    phone: str | None = None
    source: Literal["stated", "site_board"] = "stated"


@router.post("/api/parties")
def add_party(body: PartyIn):
    pid = uuid.uuid4().hex[:12]
    with db.write() as c:
        if not _row(c, "workers", body.worker_id):
            raise HTTPException(404, "WORKER_NOT_FOUND")
        c.execute("INSERT INTO parties (id, worker_id, site_id, role, name, phone, source) VALUES (?,?,?,?,?,?,?)",
                  (pid, body.worker_id, body.site_id, body.role, body.name, body.phone, body.source))
        events.append(c, "PARTY_SET", {"party_id": pid, "role": body.role, "source": body.source}, body.worker_id)
    return {"id": pid}


# --- entries -----------------------------------------------------------------

@router.post("/api/entries")
def create_entry(
    audio: UploadFile = File(...),
    kind: str = Form(...),
    worker_id: str = Form(...),
    photo: UploadFile | None = File(None),
    speaker: str = Form("worker"),
    client_ts: str | None = Form(None),
    client_sha256: str | None = Form(None),
    lat: float | None = Form(None),
    lon: float | None = Form(None),
    gps_accuracy_m: float | None = Form(None),
    gps_ts: str | None = Form(None),
    notice_played: bool = Form(False),
    notice_lang: str | None = Form(None),
    photo_client_sha256: str | None = Form(None),
    consent_refused: bool = Form(False),
):
    """Save and hash the original bytes first, then return. No model runs here.

    A thekedar or co-worker recording is accepted only if the phone played the notice / consent
    prompt first (hard rule 5): no notice, no recording.
    """
    if kind not in KINDS:
        raise HTTPException(422, "BAD_KIND")
    if speaker not in ("worker", "thekedar", "coworker"):
        raise HTTPException(422, "BAD_SPEAKER")
    if speaker in SPEAKER_KIND:
        if kind != SPEAKER_KIND[speaker]:
            raise HTTPException(422, "BAD_KIND_FOR_SPEAKER")
        if not notice_played:
            raise HTTPException(422, "NOTICE_REQUIRED")
    elif kind == "coworker_confirm":
        raise HTTPException(422, "BAD_KIND_FOR_SPEAKER")
    if consent_refused and speaker != "thekedar":
        raise HTTPException(422, "BAD_SPEAKER")  # a refusing co-worker is simply not recorded
    with db.read() as c:
        w = _row(c, "workers", worker_id)
        site = _site_for(c, worker_id)
    if not w:
        raise HTTPException(404, "WORKER_NOT_FOUND")

    data = audio.file.read()
    if not data:
        raise HTTPException(400, "EMPTY_AUDIO")
    audio_sha = _sha(data)  # hashed before anything else

    entry_id = uuid.uuid4().hex[:16]
    rel_dir = Path("media") / entry_id
    (settings.data_dir / rel_dir).mkdir(parents=True, exist_ok=True)
    audio_rel = rel_dir / f"original{_ext(audio.filename, '.webm')}"
    (settings.data_dir / audio_rel).write_bytes(data)

    photo_rec = None
    if photo is not None and photo.filename:
        pdata = photo.file.read()
        if pdata:
            photo_rel = rel_dir / f"photo{_ext(photo.filename, '.jpg')}"
            (settings.data_dir / photo_rel).write_bytes(pdata)
            psha = _sha(pdata)
            pmatch = None if not photo_client_sha256 else photo_client_sha256.strip().lower() == psha
            photo_rec = {"path": photo_rel.as_posix(), "sha256": psha, "hash_match": pmatch,
                         "kind": "payment_proof" if kind == "payment" else "photo"}

    hash_match = None if not client_sha256 else client_sha256.strip().lower() == audio_sha
    gps_saved = bool(w["gps_opt_in"]) and lat is not None and lon is not None  # GPS is opt-in only
    gps_dropped = (lat is not None or lon is not None) and not gps_saved
    lang = w["language"] if speaker == "worker" else "auto"
    server_ts = _now()

    with db.write() as c:
        c.execute(
            "INSERT INTO entries (id, worker_id, site_id, kind, speaker, language, audio_path, audio_sha256, "
            "client_sha256, hash_match, client_ts, server_ts, lat, lon, gps_accuracy_m, gps_ts, status, "
            "notice_played, notice_lang, error) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?, 'saved', ?, ?, ?)",
            (entry_id, worker_id, site["id"] if site else None, kind, speaker, lang,
             audio_rel.as_posix(), audio_sha, client_sha256, None if hash_match is None else int(hash_match),
             client_ts, server_ts, lat if gps_saved else None, lon if gps_saved else None,
             gps_accuracy_m if gps_saved else None, gps_ts if gps_saved else None,
             int(bool(notice_played)), notice_lang if notice_played else None,
             "CONSENT_REFUSED" if consent_refused else None),
        )
        events.append(c, "AUDIO_SAVED", {"entry_id": entry_id, "audio_sha256": audio_sha, "bytes": len(data),
                                         "client_sha256": client_sha256, "hash_match": hash_match,
                                         "kind": kind, "speaker": speaker},
                      worker_id, client_ts)
        if speaker == "thekedar":
            events.append(c, "THEKEDAR_RECORDED", {"entry_id": entry_id, "audio_sha256": audio_sha,
                                                   "notice_played": True, "notice_lang": notice_lang,
                                                   "consent_refused": consent_refused},
                          worker_id, client_ts)
        elif speaker == "coworker":
            events.append(c, "WITNESS_RECORDED", {"entry_id": entry_id, "audio_sha256": audio_sha,
                                                  "consent_prompt_shown": True}, worker_id, client_ts)
        if hash_match is False:
            events.append(c, "HASH_MISMATCH", {"entry_id": entry_id, "server_sha256": audio_sha,
                                               "client_sha256": client_sha256}, worker_id, client_ts)
        if photo_rec:
            pid = uuid.uuid4().hex[:12]
            c.execute("INSERT INTO evidence (id, worker_id, entry_id, kind, path, sha256, consent, lat, lon, "
                      "gps_accuracy_m, taken_ts, client_sha256, hash_match, created_at) "
                      "VALUES (?,?,?,?,?,?,1,?,?,?,?,?,?,?)",
                      (pid, worker_id, entry_id, photo_rec["kind"], photo_rec["path"], photo_rec["sha256"],
                       lat if gps_saved else None, lon if gps_saved else None,
                       gps_accuracy_m if gps_saved else None, client_ts, photo_client_sha256,
                       None if photo_rec["hash_match"] is None else int(photo_rec["hash_match"]), server_ts))
            events.append(c, "PHOTO_SAVED", {"entry_id": entry_id, "evidence_id": pid, "kind": photo_rec["kind"],
                                             "sha256": photo_rec["sha256"], "hash_match": photo_rec["hash_match"]},
                          worker_id, client_ts)
        if gps_saved:
            events.append(c, "GPS_CAPTURED", {"entry_id": entry_id, "lat": lat, "lon": lon,
                                              "accuracy_m": gps_accuracy_m}, worker_id, gps_ts)

    if processing.active() and not consent_refused:
        processing.enqueue(entry_id)  # saved + hashed above; the models run in the background, one at a time
    return {
        "entry_id": entry_id,
        "audio_sha256": audio_sha,
        "status": "saved",
        "hash_match": hash_match,
        "photo_sha256": photo_rec["sha256"] if photo_rec else None,
        "gps_saved": gps_saved,
        "gps_dropped": gps_dropped,
    }


@router.get("/api/entries/{entry_id}")
def get_entry(entry_id: str):
    with db.read() as c:
        e = _row(c, "entries", entry_id)
    if not e:
        raise HTTPException(404, "ENTRY_NOT_FOUND")
    return {**e, "processing": processing.status(entry_id), "queue_position": processing.position(entry_id)}


def _entry_or_404(c, entry_id: str) -> dict:
    e = _row(c, "entries", entry_id)
    if not e:
        raise HTTPException(404, "ENTRY_NOT_FOUND")
    return e


@router.post("/api/entries/{entry_id}/process")
def process_endpoint(entry_id: str, background: bool = Query(False, alias="async")):
    """`?async=1` (the phone): queue it and return at once; poll GET /api/entries/{id}. Without it: run now."""
    if background and processing.active():
        with db.read() as c:
            e = _entry_or_404(c, entry_id)
        if e["status"] != "saved" or e.get("error") == "CONSENT_REFUSED":
            return {"entry_id": entry_id, "status": e["status"], "processing": None}
        return {"entry_id": entry_id, "status": "saved", "processing": processing.enqueue(entry_id),
                "queue_position": processing.position(entry_id)}
    if processing.status(entry_id):
        raise HTTPException(409, "PROCESSING")  # the background worker has it: never run the models twice
    return process_entry(entry_id)


def process_entry(entry_id: str):
    """ASR → normalize → extract → reconcile. Any model failure leaves the entry `saved`."""
    with db.read() as c:
        e = _entry_or_404(c, entry_id)
        worker = _row(c, "workers", e["worker_id"])
        site = _site_for(c, e["worker_id"])
    if e["status"] == "confirmed":
        raise HTTPException(409, "ALREADY_CONFIRMED")
    if e["status"] == "deleted":
        raise HTTPException(409, "DELETED")  # a tombstone stays purged
    if e.get("error") == "CONSENT_REFUSED":
        raise HTTPException(409, "CONSENT_REFUSED")  # only the notice was kept; nothing to transcribe

    if not e["audio_path"]:
        raise HTTPException(409, "NO_AUDIO")
    original = settings.data_dir / e["audio_path"]
    wav = original.parent / "16k.wav"
    try:
        if not wav.exists():
            asr.to_wav16k(original, wav)
        asr_res = asr.transcribe_wav(wav, e["language"])
    except asr.ASRUnavailable as ex:
        return {"entry_id": entry_id, "status": e["status"], "error": ex.args[0].split(":")[0],
                "detail": str(ex), "fields": None}

    transcript = asr_res["text"]
    segments = asr_res["segments"]
    rec = _rec_date(e)
    norm = normalize.normalize(transcript, rec)
    context = {}
    if site:
        context = {"site": site.get("name"), "principal_employer": site.get("principal_employer")}
    defaults = {}
    if worker and worker.get("default_break_min") is not None and e["kind"] == "workday":
        defaults["break_minutes"] = worker["default_break_min"]

    llm_error = None
    llm = None
    if transcript.strip():  # nothing said → nothing to extract; skip the slow LLM call
        try:
            llm = extract.extract(e["kind"], transcript, rec.isoformat(), context or None)
        except extract.LLMUnavailable as ex:
            llm_error = ex.args[0]

    rec_out = reconcile.reconcile(e["kind"], llm, norm, transcript, rec, segments, defaults)
    reply = None
    if e["speaker"] == "thekedar" and transcript.strip() and not llm_error:
        try:
            reply = _ground_reply(extract.extract_reply(transcript), transcript)
        except extract.LLMUnavailable:
            reply = None  # the statement numbers still stand; the worker picks the intent
    new_status = "saved" if llm_error else "processed"
    with db.write() as c:
        c.execute(
            "UPDATE entries SET status=?, transcript=?, asr_meta=?, extraction=?, reconciled=?, error=?, reply=? "
            "WHERE id=?",
            (new_status, transcript,
             json.dumps({"language": asr_res["language"], "duration": asr_res["duration"],
                         "segments": [{k: v for k, v in s.items() if k != "words"} for s in segments]},
                        ensure_ascii=False),
             json.dumps(llm, ensure_ascii=False) if llm is not None else None,
             json.dumps(rec_out, ensure_ascii=False), llm_error,
             json.dumps(reply, ensure_ascii=False) if reply else None, entry_id),
        )
        events.append(c, "ENTRY_PROCESSED", {"entry_id": entry_id, "transcript_sha256": _sha(transcript.encode()),
                                             "llm_error": llm_error, "tier": "server"}, e["worker_id"])
    return {
        "entry_id": entry_id,
        "status": new_status,
        "transcript": transcript,
        "language": asr_res["language"],
        "fields": rec_out["fields"],
        "summary": rec_out["summary"],
        "error": llm_error,
        "tier": "server",
        "reply": reply,
    }


def _ground_reply(raw: dict, transcript: str) -> dict:
    """thekedar_reply output with every quoted field grounded (else null); intent is a classification only."""
    out = {"intent": raw.get("intent") if raw.get("intent") in REPLY_INTENTS else "other",
           "confidence": raw.get("confidence") if raw.get("confidence") in ("high", "low") else "low"}
    for name in ("amount", "date", "days"):
        f = raw.get(name) or {}
        ev = f.get("evidence")
        ok = f.get("value") not in (None, "") and reconcile._grounded(ev, transcript)
        out[name] = {"value": f.get("value") if ok else None, "evidence": ev if ok else None}
        if name in ("amount", "days") and ok:
            out[name]["value"] = normalize.parse_money(ev)  # the number is read from the quote by code
    return out


class ConfirmIn(BaseModel):
    fields: dict[str, Any]


@router.post("/api/entries/{entry_id}/confirm")
def confirm_entry(entry_id: str, body: ConfirmIn):
    with db.read() as c:
        e = _entry_or_404(c, entry_id)
    if e["status"] != "processed":
        raise HTTPException(409, "NOT_PROCESSED")
    kind = e["kind"]
    fields = dict(body.fields)
    extra: dict[str, Any] = {}
    if kind == "hisaab_statement" and e["speaker"] == "thekedar":
        intent = fields.pop("intent", None)
        if intent not in (None, "") and intent not in REPLY_INTENTS:
            raise HTTPException(422, "BAD_ENUM:intent")
        extra["intent"] = intent or None
    if kind == "coworker_confirm":
        if fields.pop("consent", None) is not True:
            raise HTTPException(422, "CONSENT_REQUIRED")  # no consent: the witness entry cannot count
        dates = fields.pop("dates", None)
        if not isinstance(dates, list) or not dates:
            raise HTTPException(422, "DATES_REQUIRED")
        try:
            dates = sorted({date.fromisoformat(str(d)).isoformat() for d in dates})
        except ValueError as ex:
            raise HTTPException(422, "BAD_DATE:dates") from ex
        if dates[-1] > date.today().isoformat():
            raise HTTPException(422, "FUTURE_DATE:dates")
        extra["dates"], extra["consent"] = dates, True
    confirmed = {name: _coerce(kind, name, v) for name, v in fields.items()}
    confirmed.update(extra)
    reconciled = (e.get("reconciled") or {}).get("fields", {})
    now = _now()
    witness = kind == "coworker_confirm"
    with db.write() as c:
        c.execute("UPDATE entries SET status='confirmed', confirmed=?, confirmed_at=?, linked_day_ids=? WHERE id=?",
                  (json.dumps(confirmed, ensure_ascii=False), now,
                   json.dumps(extra.get("dates")) if witness else None, entry_id))
        # A witness's name stays out of the chain payload (it can be redacted on export); the chain
        # commits to it through the hash of the confirmed content.
        payload = {"entry_id": entry_id, "kind": kind,
                   **({"confirmed_sha256": _sha(events.canonical(confirmed)), "dates": extra["dates"]}
                      if witness else {"confirmed": confirmed})}
        events.append(c, "ENTRY_CONFIRMED", payload, e["worker_id"])
        for name, v in confirmed.items():
            before = reconciled.get(name, {}).get("value")
            if name in reconciled and before != v and not witness:
                events.append(c, "FIELD_EDITED", {"entry_id": entry_id, "field": name, "from": before, "to": v},
                              e["worker_id"])
        if kind == "payment":
            events.append(c, "PAYMENT_CONFIRMED", {"entry_id": entry_id, "amount": confirmed.get("amount_paid")},
                          e["worker_id"])
        if witness:
            events.append(c, "COWORKER_CONFIRMED", {"entry_id": entry_id, "dates": extra["dates"],
                                                    "audio_sha256": e["audio_sha256"]}, e["worker_id"])
        if (kind == "hisaab_statement" and e["speaker"] == "thekedar" and extra.get("intent") == "promise_to_pay"
                and confirmed.get("balance_promised") is not None):
            pid = uuid.uuid4().hex[:12]
            c.execute("INSERT INTO promises (id, worker_id, source_entry_id, source, source_ref, amount, due_date, "
                      "date_status, confirmed, created_at) VALUES (?,?,?, 'recording', ?,?,?,?,1,?)",
                      (pid, e["worker_id"], entry_id, e["audio_sha256"], confirmed["balance_promised"],
                       confirmed.get("promised_date"), "stated" if confirmed.get("promised_date") else None, now))
            events.append(c, "PROMISE_LOGGED", {"promise_id": pid, "entry_id": entry_id, "source": "recording",
                                                "amount": confirmed["balance_promised"],
                                                "due": confirmed.get("promised_date")}, e["worker_id"])
        head = events.head(c)
    if kind in ("workday", "payment"):
        from . import telegram_bot  # DAILY_UPDATE / PAYMENT_ACK; never fails the confirm

        telegram_bot.on_entry_confirmed(e["worker_id"], kind, confirmed)
    return {"entry_id": entry_id, "kind": kind, "status": "confirmed", "chain_head": head}


@router.delete("/api/entries/{entry_id}")
def tombstone_entry(entry_id: str):
    """Tombstone: the row keeps its hash, the transcript and extraction are purged (Handoff §10.9)."""
    with db.write() as c:
        e = _entry_or_404(c, entry_id)
        if e["status"] == "deleted":
            return {"entry_id": entry_id, "status": "deleted"}
        c.execute("UPDATE entries SET status='deleted', transcript=NULL, extraction=NULL, reconciled=NULL, "
                  "confirmed=NULL, asr_meta=NULL WHERE id=?", (entry_id,))
        events.append(c, "ENTRY_DELETED", {"entry_id": entry_id, "content_sha256": e["audio_sha256"]},
                      e["worker_id"])
    return {"entry_id": entry_id, "status": "deleted"}


@router.post("/api/entries/copy-yesterday")
def copy_yesterday(worker_id: str = Form(...), client_ts: str = Form(...)):
    """'Same as yesterday': a workday entry copied from the last confirmed day. It has no audio, so its
    SHA-256 is over the template content. Every copied field is amber until the worker confirms it."""
    try:
        today = date.fromisoformat(client_ts[:10])
    except ValueError as e:
        raise HTTPException(422, "BAD_CLIENT_TS") from e
    with db.read() as c:
        worker = _row(c, "workers", worker_id)
        if not worker:
            raise HTTPException(404, "WORKER_NOT_FOUND")
        prev = [r for r in _confirmed(c, worker_id, None, today.isoformat()) if r["kind"] == "workday"]
        site = _site_for(c, worker_id)
    prev = sorted((r for r in prev if r["day"] < today.isoformat()), key=lambda r: r["day"])
    if not prev:
        raise HTTPException(404, "NO_PREVIOUS_DAY")
    src = prev[-1]["confirmed"]
    values = {
        "work_date": today.isoformat(),
        "start_time": src.get("start_time"),
        "end_time": src.get("end_time"),
        "break_minutes": src.get("break_minutes"),
        "worked": "yes",
        "contractor_name": src.get("contractor_name"),
    }
    fields = {}
    for name, v in values.items():
        fields[name] = {"value": v, "status": "amber" if v not in (None, "") else "none",
                        "candidates": [v] if v not in (None, "") else [], "evidence": None, "span": None,
                        "flags": ["COPIED_FROM_PREVIOUS_DAY"] if v not in (None, "") else [], "source": "copy"}
    reconciled = {"fields": fields, "summary": {"green": 0, "amber": sum(1 for f in fields.values() if f["status"] == "amber"),
                                                 "red": 0, "none": sum(1 for f in fields.values() if f["status"] == "none")}}
    template_sha = _sha(json.dumps(values, sort_keys=True, ensure_ascii=False).encode("utf-8"))
    entry_id = uuid.uuid4().hex[:16]
    server_ts = _now()
    with db.write() as c:
        c.execute(
            "INSERT INTO entries (id, worker_id, site_id, kind, speaker, language, audio_path, audio_sha256, "
            "client_ts, server_ts, status, reconciled, error) VALUES (?,?,?, 'workday', 'worker', ?, '', ?, ?, ?, "
            "'processed', ?, NULL)",
            (entry_id, worker_id, site["id"] if site else None, worker["language"], template_sha, client_ts, server_ts,
             json.dumps(reconciled, ensure_ascii=False)),
        )
        events.append(c, "ENTRY_COPIED_YESTERDAY", {"entry_id": entry_id, "from_day": src.get("work_date"),
                                                   "template_sha256": template_sha}, worker_id, client_ts)
    return {"entry_id": entry_id, "status": "processed", "fields": fields, "summary": reconciled["summary"]}


# --- ledger and hisaab -------------------------------------------------------

def _confirmed(c, worker_id: str, date_from: str | None, date_to: str | None) -> list[dict]:
    rows = c.execute(
        "SELECT * FROM entries WHERE worker_id=? AND status='confirmed' AND kind IN ('workday','payment') "
        "ORDER BY confirmed_at", (worker_id,)).fetchall()
    out = []
    for r in rows:
        d = _decode(dict(r))
        day = (d["confirmed"] or {}).get("work_date" if d["kind"] == "workday" else "payment_date")
        if day and (date_from and day < date_from or date_to and day > date_to):
            continue
        d["day"] = day
        out.append(d)
    return out


@router.get("/api/ledger")
def ledger(worker_id: str, date_from: str | None = None, date_to: str | None = None):
    with db.read() as c:
        if not _row(c, "workers", worker_id):
            raise HTTPException(404, "WORKER_NOT_FOUND")
        rows = _confirmed(c, worker_id, date_from, date_to)
        levels = day_levels(c, worker_id, [r["day"] for r in rows if r["kind"] == "workday" and r["day"]])
        proofs = {r["entry_id"]: r["n"] for r in c.execute(
            "SELECT entry_id, COUNT(*) n FROM evidence WHERE worker_id=? AND kind='payment_proof' GROUP BY entry_id",
            (worker_id,))}
        h = events.head(c)
    days = [{"entry_id": r["id"], "date": r["day"], **{k: r["confirmed"].get(k) for k in
             ("start_time", "end_time", "break_minutes", "worked")},
             "corroboration": levels.get(r["day"])}
            for r in rows if r["kind"] == "workday"]
    payments = [{"entry_id": r["id"], "date": r["day"], "amount": r["confirmed"].get("amount_paid"),
                 "mode": r["confirmed"].get("payment_mode"), "proof_photos": proofs.get(r["id"], 0)}
                for r in rows if r["kind"] == "payment"]
    return {"worker_id": worker_id, "days": days, "payments": payments, "chain_head": h,
            "corroboration_note": corroboration.DISCLAIMER}


def _day_of(ts: str | None) -> str | None:
    """Calendar date of an ISO timestamp as the phone wrote it (device time, labelled as such)."""
    if not ts:
        return None
    try:
        return date.fromisoformat(ts[:10]).isoformat()
    except ValueError:
        return None


def day_levels(c, worker_id: str, days: list[str]) -> dict[str, dict]:
    """Collect the corroboration inputs from the DB and run the deterministic rules (corroboration.py)."""
    if not days:
        return {}
    site = _site_for(c, worker_id)
    site_pt = {"lat": site["site_lat"], "lon": site["site_lon"]} if site and site.get("site_lat") is not None else None
    photos = [{"day": _day_of(r["taken_ts"] or r["created_at"]), "lat": r["lat"], "lon": r["lon"],
               "acc": r["gps_accuracy_m"], "ref": r["sha256"]}
              for r in c.execute("SELECT * FROM evidence WHERE worker_id=? AND kind IN ('photo','site_board')",
                                 (worker_id,))]
    fixes, coworker, thekedar = [], [], []
    for r in c.execute("SELECT * FROM entries WHERE worker_id=? AND status='confirmed'", (worker_id,)):
        r = _decode(dict(r))
        if r["lat"] is not None:
            fixes.append({"day": _day_of(r["gps_ts"] or r["client_ts"]), "lat": r["lat"], "lon": r["lon"],
                          "acc": r["gps_accuracy_m"], "ref": r["audio_sha256"]})
        cf = r["confirmed"] or {}
        if r["kind"] == "coworker_confirm" and cf.get("consent"):
            coworker.append({"dates": cf.get("dates") or [], "ref": r["audio_sha256"]})
        elif r["kind"] == "hisaab_statement" and r["speaker"] == "thekedar":
            thekedar.append({"rec_day": _day_of(r["client_ts"] or r["server_ts"]),
                             "days_counted": cf.get("days_counted"), "intent": cf.get("intent"),
                             "ref": r["audio_sha256"]})
    # Telegram: a promise counts once the worker confirmed it; a dispute shows until the worker dismisses it.
    from .telegram_bot import local_day

    for r in c.execute("SELECT kind, status, tg_date, message_sha256 FROM inbox WHERE worker_id=? AND "
                       "((kind='promise' AND status='confirmed') OR (kind='dispute' AND status IN ('new','seen')))",
                       (worker_id,)):
        thekedar.append({"rec_day": local_day(r["tg_date"]), "days_counted": None, "ref": r["message_sha256"],
                         "intent": "promise_to_pay" if r["kind"] == "promise" else "disputes_days"})
    return corroboration.compute_levels(days, site=site_pt, photos=[p for p in photos if p["day"]],
                                        fixes=[f for f in fixes if f["day"]], coworker=coworker,
                                        thekedar=[t for t in thekedar if t["rec_day"]])


@router.get("/api/hisaab")
def hisaab(worker_id: str, date_from: str | None = None, date_to: str | None = None):
    """Wraps the deterministic wage engine. Errors come back as codes, never as amounts."""
    with db.read() as c:
        worker = _row(c, "workers", worker_id)
        if not worker:
            raise HTTPException(404, "WORKER_NOT_FOUND")
        site = _site_for(c, worker_id)
        rows = _confirmed(c, worker_id, date_from, date_to)
    if not site:
        return {"ok": False, "errors": ["SITE_NOT_SET"], "days": [], "totals": None}

    days, excluded, payments = [], [], []
    for r in rows:
        cf = r["confirmed"]
        if r["kind"] == "workday":
            if cf.get("worked") == "no":
                continue
            if not (r["day"] and cf.get("start_time") and cf.get("end_time")):
                excluded.append({"entry_id": r["id"], "reason": "MISSING_DATE_OR_TIME"})
                continue
            brk = cf.get("break_minutes")
            if brk is None:
                excluded.append({"entry_id": r["id"], "reason": "BREAK_NOT_CONFIRMED"})
                continue
            days.append(WorkDay(date.fromisoformat(r["day"]), parse_time(cf["start_time"]),
                                parse_time(cf["end_time"]), int(brk), r["id"]))
        else:
            if not (r["day"] and cf.get("amount_paid") is not None):
                excluded.append({"entry_id": r["id"], "reason": "MISSING_DATE_OR_AMOUNT"})
                continue
            payments.append(Payment(date.fromisoformat(r["day"]), str(cf["amount_paid"]), r["id"]))

    ctx = RateContext(
        sphere=site["sphere"],
        state=site["state"],
        employment_sn=site["employment_sn"],
        category=worker["category"],
        zone=site["zone"],
        zone_confirmed=bool(site["zone_confirmed"]),
    )
    res = compute(days, payments, ctx, load_packs(), wage_period=site["wage_period"])
    res["excluded_entries"] = excluded
    return json.loads(json.dumps(res, default=str))


# --- chain -------------------------------------------------------------------

@router.get("/api/chain/verify")
def chain_verify():
    with db.read() as c:
        return events.verify(c)


# --- internal: model-server mode for a cloud GPU (ASR_MODE=remote on the laptop) ----

@router.post("/internal/asr")
def internal_asr(audio: UploadFile = File(...), language: str = Form("auto")):
    if language not in ("hi", "mr", "auto"):
        raise HTTPException(422, "BAD_LANGUAGE")
    tmp = settings.data_dir / "tmp" / uuid.uuid4().hex
    tmp.mkdir(parents=True, exist_ok=True)
    src = tmp / f"in{_ext(audio.filename, '.bin')}"
    src.write_bytes(audio.file.read())
    try:
        wav = asr.to_wav16k(src, tmp / "16k.wav")
        return asr.transcribe_wav(wav, language)
    except asr.ASRUnavailable as ex:
        raise HTTPException(503, str(ex)) from ex
