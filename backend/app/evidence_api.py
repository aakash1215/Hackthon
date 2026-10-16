"""P3 API: evidence photos (payment proof, site board), hisaab-check differences, coach checklist,
evidence packet export.

Same order as entries: original bytes are hashed and saved before anything else.
"""
from __future__ import annotations

import json
import uuid
from datetime import date
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from . import db, events, hisaab_check, packet
from .api import _confirmed, _decode, _ext, _now, _row, _sha, _site_for, hisaab
from .config import settings

router = APIRouter()
PHOTO_KINDS = ("photo", "payment_proof", "site_board")


# --- photos --------------------------------------------------------------------

@router.post("/api/evidence/photo")
def add_photo(
    photo: UploadFile = File(...),
    worker_id: str = Form(...),
    kind: str = Form("photo"),
    entry_id: str | None = Form(None),
    client_ts: str | None = Form(None),
    client_sha256: str | None = Form(None),
    caption: str | None = Form(None),
    lat: float | None = Form(None),
    lon: float | None = Form(None),
    gps_accuracy_m: float | None = Form(None),
):
    """A photo on its own or attached to an entry: payment proof (UPI/SMS/slip) or the site board."""
    if kind not in PHOTO_KINDS:
        raise HTTPException(422, "BAD_KIND")
    with db.read() as c:
        w = _row(c, "workers", worker_id)
        if not w:
            raise HTTPException(404, "WORKER_NOT_FOUND")
        if entry_id:
            e = _row(c, "entries", entry_id)
            if not e or e["worker_id"] != worker_id:
                raise HTTPException(404, "ENTRY_NOT_FOUND")
            if kind == "payment_proof" and e["kind"] != "payment":
                raise HTTPException(422, "NOT_A_PAYMENT")
    data = photo.file.read()
    if not data:
        raise HTTPException(400, "EMPTY_PHOTO")
    sha = _sha(data)  # hashed before anything else
    eid = uuid.uuid4().hex[:12]
    rel = Path("media") / "evidence" / f"{eid}{_ext(photo.filename, '.jpg')}"
    (settings.data_dir / rel).parent.mkdir(parents=True, exist_ok=True)
    (settings.data_dir / rel).write_bytes(data)
    match = None if not client_sha256 else client_sha256.strip().lower() == sha
    gps_ok = bool(w["gps_opt_in"]) and lat is not None and lon is not None
    with db.write() as c:
        c.execute("INSERT INTO evidence (id, worker_id, entry_id, kind, path, sha256, caption, consent, lat, lon, "
                  "gps_accuracy_m, taken_ts, client_sha256, hash_match, created_at) "
                  "VALUES (?,?,?,?,?,?,?,1,?,?,?,?,?,?,?)",
                  (eid, worker_id, entry_id, kind, rel.as_posix(), sha, (caption or "")[:200] or None,
                   lat if gps_ok else None, lon if gps_ok else None, gps_accuracy_m if gps_ok else None,
                   client_ts, client_sha256, None if match is None else int(match), _now()))
        events.append(c, "PHOTO_SAVED", {"evidence_id": eid, "entry_id": entry_id, "kind": kind, "sha256": sha,
                                         "hash_match": match}, worker_id, client_ts)
        if match is False:
            events.append(c, "HASH_MISMATCH", {"evidence_id": eid, "server_sha256": sha,
                                               "client_sha256": client_sha256}, worker_id, client_ts)
        if gps_ok:
            events.append(c, "GPS_CAPTURED", {"evidence_id": eid, "lat": lat, "lon": lon,
                                              "accuracy_m": gps_accuracy_m}, worker_id, client_ts)
    return {"evidence_id": eid, "sha256": sha, "hash_match": match, "kind": kind, "gps_saved": gps_ok}


@router.get("/api/evidence")
def list_evidence(worker_id: str, kind: str | None = None):
    with db.read() as c:
        q = "SELECT id, entry_id, kind, sha256, caption, lat, lon, gps_accuracy_m, taken_ts, created_at, hash_match " \
            "FROM evidence WHERE worker_id=?"
        args: list = [worker_id]
        if kind:
            q += " AND kind=?"
            args.append(kind)
        return {"items": [dict(r) for r in c.execute(q + " ORDER BY created_at", args)]}


@router.get("/api/evidence/{evidence_id}/file")
def evidence_file(evidence_id: str):
    with db.read() as c:
        r = _row(c, "evidence", evidence_id)
    if not r or r["kind"] == "witness_audio":
        raise HTTPException(404, "NOT_FOUND")
    return FileResponse(settings.data_dir / r["path"])


class BoardIn(BaseModel):
    worker_id: str
    principal_employer: str | None = None
    maharera_no: str | None = None


@router.post("/api/sites/board")
def site_board(body: BoardIn):
    """Builder name / MahaRERA number read off the site board by the worker (source: site_board)."""
    with db.write() as c:
        site = _site_for(c, body.worker_id)
        if not site:
            raise HTTPException(404, "SITE_NOT_SET")
        pe = (body.principal_employer or "").strip()[:120] or site["principal_employer"]
        rera = (body.maharera_no or "").strip()[:40] or site["maharera_no"]
        c.execute("UPDATE sites SET principal_employer=?, maharera_no=? WHERE id=?", (pe, rera, site["id"]))
        if body.principal_employer:
            c.execute("INSERT INTO parties (id, worker_id, site_id, role, name, source) "
                      "VALUES (?,?,?, 'principal_employer', ?, 'site_board')",
                      (uuid.uuid4().hex[:12], body.worker_id, site["id"], pe))
        events.append(c, "SITE_BOARD_SET", {"site_id": site["id"], "principal_employer": pe, "maharera_no": rera},
                      body.worker_id)
    return {"site_id": site["id"], "principal_employer": pe, "maharera_no": rera}


# --- hisaab check ----------------------------------------------------------------

def _window_for(entry: dict) -> tuple[str, str]:
    """The ledger window a settlement statement speaks about: its month, up to the statement date."""
    d = (entry.get("client_ts") or entry["server_ts"])[:10]
    return d[:8] + "01", d


def differences_for(c, entry: dict) -> dict:
    d_from, d_to = _window_for(entry)
    rows = _confirmed(c, entry["worker_id"], d_from, d_to)
    days = sorted({r["day"] for r in rows if r["kind"] == "workday" and r["day"]
                   and (r["confirmed"] or {}).get("worked") != "no"})
    paid = sum(int((r["confirmed"] or {}).get("amount_paid") or 0) for r in rows if r["kind"] == "payment")
    noted = any((r["confirmed"] or {}).get("deductions") for r in rows if r["kind"] == "payment")
    engine = hisaab(entry["worker_id"], d_from, d_to)
    out = hisaab_check.compare(entry["confirmed"] or {}, days, paid, engine, noted)
    out.update({"entry_id": entry["id"], "speaker": entry["speaker"], "window": [d_from, d_to],
                "statement": entry["confirmed"], "provenance": (engine.get("provenance") or [None])[0]})
    return out


@router.get("/api/entries/{entry_id}/differences")
def differences(entry_id: str):
    with db.read() as c:
        e = _row(c, "entries", entry_id)
        if not e or e["kind"] != "hisaab_statement":
            raise HTTPException(404, "STATEMENT_NOT_FOUND")
        if e["status"] != "confirmed":
            raise HTTPException(409, "NOT_CONFIRMED")
        return differences_for(c, e)


@router.get("/api/statements")
def statements(worker_id: str):
    """Confirmed settlement statements (worker-narrated and thekedar recordings), newest first."""
    with db.read() as c:
        rows = [_decode(dict(r)) for r in c.execute(
            "SELECT * FROM entries WHERE worker_id=? AND kind='hisaab_statement' AND status='confirmed' "
            "ORDER BY confirmed_at DESC", (worker_id,))]
        return {"items": [{"entry_id": r["id"], "speaker": r["speaker"], "confirmed_at": r["confirmed_at"],
                           "count": differences_for(c, r)["count"]} for r in rows]}


class ManualIn(BaseModel):
    worker_id: str
    kind: str = "hisaab_statement"
    client_ts: str


@router.post("/api/entries/manual")
def manual_entry(body: ManualIn):
    """'टाइप करके भरें' (UI/ H3): an empty settlement statement the worker fills on the confirm card.
    There is no audio; its SHA-256 is over the creation record and every field starts empty."""
    if body.kind != "hisaab_statement":
        raise HTTPException(422, "BAD_KIND")
    try:
        date.fromisoformat(body.client_ts[:10])
    except ValueError as e:
        raise HTTPException(422, "BAD_CLIENT_TS") from e
    with db.read() as c:
        w = _row(c, "workers", body.worker_id)
        site = _site_for(c, body.worker_id)
    if not w:
        raise HTTPException(404, "WORKER_NOT_FOUND")
    eid = uuid.uuid4().hex[:16]
    sha = _sha(json.dumps({"entry_id": eid, "kind": body.kind, "client_ts": body.client_ts, "typed": True},
                          sort_keys=True).encode())
    with db.write() as c:
        c.execute("INSERT INTO entries (id, worker_id, site_id, kind, speaker, language, audio_path, audio_sha256, "
                  "client_ts, server_ts, status, reconciled) VALUES (?,?,?,?, 'worker', ?, '', ?, ?, ?, 'processed', ?)",
                  (eid, body.worker_id, site["id"] if site else None, body.kind, w["language"], sha, body.client_ts,
                   _now(), json.dumps({"fields": {}, "summary": {}})))
        events.append(c, "ENTRY_TYPED", {"entry_id": eid, "kind": body.kind, "sha256": sha}, body.worker_id,
                      body.client_ts)
    return {"entry_id": eid, "status": "processed"}


# --- coach checklist (Handoff §10.14; never a legal score) ------------------------

@router.get("/api/coach")
def coach(worker_id: str):
    with db.read() as c:
        w = _row(c, "workers", worker_id)
        if not w:
            raise HTTPException(404, "WORKER_NOT_FOUND")
        return packet.coach_items(c, w)


# --- packet ------------------------------------------------------------------------

class ExportIn(BaseModel):
    worker_id: str
    date_from: str | None = None
    date_to: str | None = None
    redact_witness_names: bool = True
    include_witness_audio: bool = False


@router.post("/api/export")
def export(body: ExportIn):
    """Evidence packet: Jinja2 HTML → PDF (Playwright/Chromium) + bundle.zip with a hash manifest."""
    with db.read() as c:
        if not _row(c, "workers", body.worker_id):
            raise HTTPException(404, "WORKER_NOT_FOUND")
    return packet.build(body.worker_id, body.date_from, body.date_to,
                        redact_witness_names=body.redact_witness_names,
                        include_witness_audio=body.include_witness_audio)


@router.get("/api/exports/{export_id}/{name}")
def export_file(export_id: str, name: str):
    if name not in ("packet.pdf", "packet.html", "bundle.zip"):
        raise HTTPException(404, "NOT_FOUND")
    if not export_id.isalnum():
        raise HTTPException(404, "NOT_FOUND")
    f = settings.data_dir / "exports" / export_id / name
    if not f.is_file():
        raise HTTPException(404, "NOT_FOUND")
    media = {"packet.pdf": "application/pdf", "packet.html": "text/html; charset=utf-8",
             "bundle.zip": "application/zip"}[name]
    return FileResponse(f, media_type=media, filename=name if name != "packet.html" else None)
