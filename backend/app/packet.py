"""Evidence packet (Handoff §10.13 + BUILD_PLAN P3): Jinja2 HTML → PDF (Playwright/Chromium) + bundle.zip.

Everything in the packet is either a worker-confirmed value, a verbatim transcript, a hash, or a number
from the deterministic wage engine. Wording: "evidence file", "corroborated record", "estimate".
Witness (co-worker) audio is never bundled by default, and witness names can be redacted.
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
import logging
import uuid
import zipfile
from datetime import date, datetime, timedelta
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from . import corroboration, db, events
from .config import settings

log = logging.getLogger("apna_hisaab.packet")
APP_DIR = Path(__file__).resolve().parent
FONT_DIR = APP_DIR / "static" / "fonts"
_env = Environment(loader=FileSystemLoader(APP_DIR / "templates"), autoescape=select_autoescape(["html", "j2"]))

INTENT_HI = {
    "acknowledges": "दिन/रक़म माने", "promise_to_pay": "पैसे देने का वादा", "partial_payment_claim": "कहा कुछ दिया है",
    "disputes_days": "दिन नहीं माने", "disputes_rate": "दर नहीं मानी", "asks_details": "ब्योरा माँगा",
    "refuses": "मना किया", "hostile": "धमकी/गाली", "other": "अन्य",
}
INTENT_EN = {
    "acknowledges": "acknowledges", "promise_to_pay": "promise to pay", "partial_payment_claim": "claims partial payment",
    "disputes_days": "disputes days", "disputes_rate": "disputes rate", "asks_details": "asks for details",
    "refuses": "refuses", "hostile": "hostile", "other": "other",
}
DIFF_LABEL = {
    "DAYS_DIFF": ("काम के दिन", "Days worked"),
    "RATE_BELOW_MIN": ("रोज़ की दर", "Daily rate vs statutory minimum"),
    "OT_NOT_COUNTED": ("ओवरटाइम", "Overtime hours not counted"),
    "DEDUCTION_DISPUTED": ("उचल / कटौती", "Advance / deduction claimed"),
    "PAID_DIFF": ("कितना दिया", "Amount paid"),
}
SIGNAL_EN = {"SELF": "worker's confirmed entry", "PHOTO": "photo that day", "GPS_AT_SITE": "GPS at site",
             "COWORKER": "co-worker confirmation", "THEKEDAR_ACK": "thekedar acknowledgement"}


def _sha_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _font_face() -> str:
    """@font-face rules with the bundled Noto Sans Devanagari as data URIs (no network, no CDN)."""
    rules = []
    for weight in (400, 700):
        for subset, rng in (("devanagari", "U+0900-097F,U+1CD0-1CF9,U+200C-200D,U+20A8,U+20B9,U+25CC,U+A830-A839,U+A8E0-A8FF"),
                            ("latin", "U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+2000-206F,U+20AC,U+2122,U+2212")):
            f = FONT_DIR / f"noto-sans-devanagari-{subset}-{weight}-normal.woff2"
            if f.exists():
                b64 = base64.b64encode(f.read_bytes()).decode()
                rules.append("@font-face{font-family:'Noto Sans Devanagari';font-weight:%d;font-style:normal;"
                             "src:url(data:font/woff2;base64,%s) format('woff2');unicode-range:%s}" % (weight, b64, rng))
    return "\n".join(rules)


def _thumb(path: Path) -> str | None:
    """Small JPEG data URI for the packet. The original file (with EXIF) goes in the bundle untouched."""
    try:
        from PIL import Image, ImageOps

        with Image.open(path) as im:
            im = ImageOps.exif_transpose(im)
            im.thumbnail((360, 360))
            buf = io.BytesIO()
            im.convert("RGB").save(buf, "JPEG", quality=70)
        return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
    except Exception:  # noqa: BLE001 — a broken image must not stop the packet
        return None


def _rows(c, sql: str, args=()) -> list[dict]:
    from .api import _decode

    return [_decode(dict(r)) for r in c.execute(sql, args)]


# --- coach (Handoff §10.14) --------------------------------------------------------

def coach_items(c, worker: dict) -> dict:
    from .api import _confirmed, _site_for

    wid = worker["id"]
    site = _site_for(c, wid) or {}
    parties = [dict(r) for r in c.execute("SELECT * FROM parties WHERE worker_id=?", (wid,))]
    contractor = next((p for p in parties if p["role"] in ("contractor", "mukadam", "subcontractor") and p["name"]), None)
    rows = _confirmed(c, wid, None, None)
    n_days = sum(1 for r in rows if r["kind"] == "workday")
    n_pay = sum(1 for r in rows if r["kind"] == "payment")
    counts = {r["k"]: r["n"] for r in c.execute(
        "SELECT kind || ':' || speaker AS k, COUNT(*) n FROM entries WHERE worker_id=? AND status='confirmed' "
        "GROUP BY kind, speaker", (wid,))}
    board = c.execute("SELECT COUNT(*) FROM evidence WHERE worker_id=? AND kind='site_board'", (wid,)).fetchone()[0]
    week_ago = (datetime.now().astimezone() - timedelta(days=7)).isoformat(timespec="seconds")
    anchored = c.execute("SELECT COUNT(*) FROM events WHERE worker_id=? AND type IN ('EXPORT_CREATED','TG_MESSAGE_OUT',"
                         "'ANCHOR_SENT') AND ts_server >= ?", (wid, week_ago[:19])).fetchone()[0]
    items = [
        {"id": "site", "ok": bool(site.get("name")), "label_hi": "साइट का नाम और पहचान", "action": None},
        {"id": "zone", "ok": bool(site.get("zone") and site.get("zone_confirmed") and site.get("sphere") != "unknown"),
         "label_hi": "साइट, ज़ोन पक्के", "action": None},
        {"id": "category", "ok": bool(worker.get("category")), "label_hi": "काम की श्रेणी पक्की", "action": None},
        {"id": "contractor", "ok": bool(contractor), "label_hi": "ठेकेदार का नाम", "action": "thekedar_phone"},
        {"id": "contractor_phone", "ok": any(p["phone"] for p in parties), "label_hi": "ठेकेदार का फ़ोन नंबर",
         "action": "thekedar_phone"},
        {"id": "site_board", "ok": bool(board or site.get("principal_employer") or site.get("maharera_no")),
         "label_hi": "बिल्डर / साइट बोर्ड की फ़ोटो", "action": "site_board"},
        {"id": "pay_period", "ok": site.get("wage_period") not in (None, "unknown"), "label_hi": "पगार कब मिलती है (हफ़्ता/महीना)",
         "action": None},
        {"id": "days", "ok": n_days > 0, "label_hi": f"{n_days} दिन का काम पक्का", "action": "record_day"},
        {"id": "payments", "ok": n_pay > 0, "label_hi": f"{n_pay} बार पैसा दर्ज", "action": "payment"},
        {"id": "witness", "ok": counts.get("coworker_confirm:coworker", 0) > 0, "label_hi": "किसी साथी की गवाही",
         "action": "coworker"},
        {"id": "hisaab", "ok": counts.get("hisaab_statement:worker", 0) + counts.get("hisaab_statement:thekedar", 0) > 0,
         "label_hi": "ठेकेदार का हिसाब दर्ज", "action": "hisaab_check"},
        {"id": "anchor", "ok": anchored > 0, "label_hi": "रिकॉर्ड कोड बाहर भेजा (7 दिन में)", "action": None},
    ]
    return {"done": sum(1 for i in items if i["ok"]), "total": len(items), "items": items,
            "note": "Packet completeness, not a legal score."}


# --- build ---------------------------------------------------------------------------

def _gather(c, worker_id: str, d_from: str, d_to: str, redact: bool) -> dict:
    from .api import _confirmed, _site_for, day_levels, hisaab
    from .evidence_api import differences_for

    worker = dict(c.execute("SELECT * FROM workers WHERE id=?", (worker_id,)).fetchone())
    site = _site_for(c, worker_id) or {}
    parties = [dict(r) for r in c.execute("SELECT * FROM parties WHERE worker_id=?", (worker_id,))]
    rows = _confirmed(c, worker_id, d_from, d_to)
    engine = hisaab(worker_id, d_from, d_to)
    eng_days = {r["date"]: r for r in engine.get("days", [])}
    levels = day_levels(c, worker_id, [r["day"] for r in rows if r["kind"] == "workday" and r["day"]])
    seq_of = {}
    for ev in c.execute("SELECT seq, payload_json FROM events WHERE worker_id=? AND type IN "
                        "('AUDIO_SAVED','ENTRY_CONFIRMED','PHOTO_SAVED','ENTRY_COPIED_YESTERDAY','ENTRY_TYPED')",
                        (worker_id,)):
        p = json.loads(ev["payload_json"])
        for k in ("entry_id", "evidence_id"):
            if p.get(k):
                seq_of.setdefault(p[k], []).append(ev["seq"])
    edits = {}
    for ev in c.execute("SELECT payload_json FROM events WHERE worker_id=? AND type='FIELD_EDITED'", (worker_id,)):
        p = json.loads(ev["payload_json"])
        if p.get("from") is not None:  # a value the worker changed; filling an empty field is not an edit
            edits.setdefault(p["entry_id"], []).append(p["field"])

    photos_all = _rows(c, "SELECT * FROM evidence WHERE worker_id=? AND kind IN ('photo','payment_proof','site_board') "
                          "ORDER BY created_at", (worker_id,))
    photos_by_entry: dict[str, list] = {}
    for p in photos_all:
        if p["entry_id"]:
            photos_by_entry.setdefault(p["entry_id"], []).append(p)

    pay_by_day: dict[str, list] = {}
    for r in rows:
        if r["kind"] == "payment" and r["day"]:
            pay_by_day.setdefault(r["day"], []).append(r)

    day_rows = []
    for r in sorted((r for r in rows if r["kind"] == "workday"), key=lambda x: x["day"] or ""):
        cf = r["confirmed"] or {}
        er = eng_days.get(r["day"], {})
        pays = pay_by_day.get(r["day"], [])
        lv = levels.get(r["day"]) or {}
        day_rows.append({
            "date": r["day"], "start": cf.get("start_time"), "end": cf.get("end_time"),
            "break": cf.get("break_minutes"), "hours": er.get("hours"), "ot": er.get("ot_hours"),
            "due": er.get("due_statutory"), "paid": sum(int(p["confirmed"].get("amount_paid") or 0) for p in pays) or None,
            "mode": ", ".join(sorted({p["confirmed"].get("payment_mode") or "?" for p in pays})) or None,
            "evidence_ids": [r["audio_sha256"][:8]] + [p["sha256"][:8] for p in photos_by_entry.get(r["id"], [])],
            "seqs": seq_of.get(r["id"], []), "confirmed_at": r["confirmed_at"], "edits": edits.get(r["id"], []),
            "copied": not r["audio_path"], "level": lv.get("level", 1), "signals": lv.get("signals", ["SELF"]),
            "flags": lv.get("flags", []), "transcript": r["transcript"],
        })
    payment_rows = [{"date": r["day"], "amount": (r["confirmed"] or {}).get("amount_paid"),
                     "mode": (r["confirmed"] or {}).get("payment_mode"), "payer": (r["confirmed"] or {}).get("payer_name"),
                     "deductions": (r["confirmed"] or {}).get("deductions"), "sha": r["audio_sha256"],
                     "transcript": r["transcript"], "proofs": photos_by_entry.get(r["id"], [])}
                    for r in rows if r["kind"] == "payment"]

    def in_period(ts: str | None) -> bool:
        d = (ts or "")[:10]
        return bool(d) and d_from <= d <= d_to

    statements = _rows(c, "SELECT * FROM entries WHERE worker_id=? AND kind='hisaab_statement' AND status='confirmed' "
                          "ORDER BY client_ts", (worker_id,))
    thekedar_words, worker_checks = [], []
    for s in statements:
        if not in_period(s["client_ts"] or s["server_ts"]):
            continue
        item = {"entry": s, "diff": differences_for(c, s), "intent": (s["confirmed"] or {}).get("intent")}
        (thekedar_words if s["speaker"] == "thekedar" else worker_checks).append(item)

    coworkers = []
    for i, e in enumerate(_rows(c, "SELECT * FROM entries WHERE worker_id=? AND kind='coworker_confirm' "
                                    "AND status='confirmed' ORDER BY confirmed_at", (worker_id,)), start=1):
        cf = e["confirmed"] or {}
        if not any(d_from <= d <= d_to for d in cf.get("dates") or []):
            continue
        coworkers.append({"name": f"साथी {i} / Co-worker {i} (name redacted)" if redact else cf.get("coworker_name") or "—",
                          "dates": cf.get("dates") or [], "consent": cf.get("consent"), "sha": e["audio_sha256"],
                          "transcript": None if redact else e["transcript"], "confirmed_at": e["confirmed_at"]})

    tg = []
    try:
        tg = _rows(c, "SELECT * FROM tg_messages WHERE worker_id=? ORDER BY tg_date", (worker_id,))
        tg = [m for m in tg if in_period(m["tg_date"])]
    except Exception:  # noqa: BLE001 — table arrives with P4
        tg = []
    promises = _rows(c, "SELECT * FROM promises WHERE worker_id=? ORDER BY created_at", (worker_id,))

    photos = []
    for p in photos_all:
        if not in_period(p["taken_ts"] or p["created_at"]) and p["kind"] != "site_board":
            continue
        photos.append({**p, "thumb": _thumb(settings.data_dir / p["path"]), "seqs": seq_of.get(p["id"], [])})

    transcripts = [{"date": r["day"], "kind": r["kind"], "text": r["transcript"], "sha": r["audio_sha256"],
                    "lang": r["language"]} for r in sorted(rows, key=lambda x: x["day"] or "") if r["transcript"]]
    verify = events.verify(c)
    return {
        "worker": worker, "site": site, "parties": parties, "engine": engine,
        "provenance": (engine.get("provenance") or [None])[0] if engine.get("ok") else None,
        "days": day_rows, "payments": payment_rows, "thekedar_words": thekedar_words, "worker_checks": worker_checks,
        "coworkers": coworkers, "tg": tg, "promises": promises, "photos": photos, "transcripts": transcripts,
        "verify": verify, "levels_note": corroboration.DISCLAIMER,
    }


def _render_pdf(html_path: Path, pdf_path: Path) -> str | None:
    """Chromium print via Playwright. Returns an error code instead of raising."""
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page()
            page.goto(html_path.resolve().as_uri(), wait_until="load")
            page.evaluate("document.fonts.ready")
            page.pdf(path=str(pdf_path), format="A4", print_background=True,
                     margin={"top": "14mm", "bottom": "16mm", "left": "12mm", "right": "12mm"},
                     display_header_footer=True, header_template="<span></span>",
                     footer_template="<div style='font-size:8px;width:100%;text-align:center;color:#666'>"
                                     "Apna Hisaab evidence file · page <span class='pageNumber'></span>/"
                                     "<span class='totalPages'></span></div>")
            browser.close()
        return None
    except Exception as e:  # noqa: BLE001 — fallback is the browser's Print-to-PDF of packet.html
        log.warning("PDF render failed: %s", e)
        return f"PDF_UNAVAILABLE:{type(e).__name__}"


def build(worker_id: str, date_from: str | None, date_to: str | None, *, redact_witness_names: bool = True,
          include_witness_audio: bool = False) -> dict:
    from .api import _confirmed, _now

    with db.read() as c:
        if not date_from or not date_to:
            days = sorted(r["day"] for r in _confirmed(c, worker_id, None, None) if r["day"])
            today = date.today().isoformat()
            date_from = date_from or (days[0] if days else today[:8] + "01")
            date_to = date_to or max(today, days[-1] if days else today)
        data = _gather(c, worker_id, date_from, date_to, redact_witness_names)
        media = _rows(c, "SELECT id, kind, speaker, audio_path, audio_sha256 FROM entries WHERE worker_id=? "
                         "AND status='confirmed' AND audio_path != ''", (worker_id,))
        chain = [dict(r) for r in c.execute("SELECT * FROM events ORDER BY seq")]

    export_id = uuid.uuid4().hex[:12]
    out = settings.data_dir / "exports" / export_id
    out.mkdir(parents=True, exist_ok=True)
    generated = _now()
    head = data["verify"].get("head") or {}
    html = _env.get_template("packet.html.j2").render(
        **data, period=(date_from, date_to), generated=generated, export_id=export_id, demo=settings.demo_mode,
        font_face=_font_face(), intent_hi=INTENT_HI, intent_en=INTENT_EN, diff_label=DIFF_LABEL, signal_en=SIGNAL_EN,
        redacted=redact_witness_names, chain_head=head,
    )
    html_path = out / "packet.html"
    html_path.write_text(html, encoding="utf-8")
    pdf_path = out / "packet.pdf"
    errors = []
    err = _render_pdf(html_path, pdf_path)
    if err:
        errors.append(err)

    # bundle.zip: packet + originals (byte-for-byte) + chain export + manifest of SHA-256s
    files: list[tuple[str, Path | bytes, str]] = [("packet.html", html_path, "packet")]
    if pdf_path.exists():
        files.append(("packet.pdf", pdf_path, "packet"))
    for m in media:
        if m["speaker"] == "coworker" and not include_witness_audio:
            continue  # witness audio is never shared by default (BUILD_PLAN §9)
        p = settings.data_dir / m["audio_path"]
        if p.exists():
            files.append((f"media/{m['id']}_{m['speaker']}{p.suffix}", p, f"audio:{m['kind']}"))
    for ph in data["photos"]:
        p = settings.data_dir / ph["path"]
        if p.exists():
            files.append((f"media/{ph['id']}_{ph['kind']}{p.suffix}", p, f"photo:{ph['kind']}"))
    chain_bytes = "\n".join(json.dumps(e, ensure_ascii=False, sort_keys=True) for e in chain).encode("utf-8")
    files.append(("chain/events.jsonl", chain_bytes, "chain"))

    manifest_items = []
    for name, src, kind in files:
        b = src if isinstance(src, bytes) else None
        sha = hashlib.sha256(b).hexdigest() if b is not None else _sha_file(src)
        size = len(b) if b is not None else src.stat().st_size
        manifest_items.append({"path": name, "sha256": sha, "bytes": size, "kind": kind})
    rate_sha = (data["provenance"] or {}).get("pack_sha256")
    manifest = {
        "export_id": export_id, "worker_id": worker_id, "period": [date_from, date_to], "generated": generated,
        "chain_head": head.get("hash"), "chain_ok": data["verify"].get("ok"), "rate_pack_sha256": rate_sha,
        "synthetic_demo_data": settings.demo_mode, "witness_names_redacted": redact_witness_names,
        "witness_audio_included": include_witness_audio, "files": manifest_items,
        "note": "SHA-256 of each file as bundled. Originals are byte-for-byte what the phone recorded.",
    }
    manifest_bytes = json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8")
    manifest_sha = hashlib.sha256(manifest_bytes).hexdigest()
    zip_path = out / "bundle.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for name, src, _ in files:
            if isinstance(src, bytes):
                z.writestr(name, src)
            else:
                z.write(src, name)
        z.writestr("manifest.json", manifest_bytes)
        z.writestr("README.txt", (
            "Apna Hisaab evidence file\n"
            + ("SYNTHETIC DEMO DATA\n" if settings.demo_mode else "")
            + f"Period {date_from} to {date_to}. manifest.json lists the SHA-256 of every file.\n"
            "chain/events.jsonl is the append-only hash chain: hash = sha256(prev_hash + canonical event).\n"
            "Prepared from the worker's own records; computed by fixed rules; not legal advice; "
            "not verified by any authority.\n").encode("utf-8"))

    with db.write() as c:
        c.execute("INSERT INTO exports (id, worker_id, period_from, period_to, pdf_path, html_path, zip_path, "
                  "manifest_sha256, chain_head, rate_pack_sha256, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                  (export_id, worker_id, date_from, date_to,
                   str(pdf_path) if pdf_path.exists() else None, str(html_path), str(zip_path), manifest_sha,
                   head.get("hash"), rate_sha, generated))
        events.append(c, "EXPORT_CREATED", {"export_id": export_id, "period": [date_from, date_to],
                                            "manifest_sha256": manifest_sha, "chain_head": head.get("hash"),
                                            "witness_names_redacted": redact_witness_names}, worker_id)
    base = f"/api/exports/{export_id}"
    return {
        "export_id": export_id, "period": [date_from, date_to],
        "pdf_url": f"{base}/packet.pdf" if pdf_path.exists() else None,
        "html_url": f"{base}/packet.html", "zip_url": f"{base}/bundle.zip",
        "manifest_sha256": manifest_sha, "chain_head": {"hash": head.get("hash"), "short": head.get("short")},
        "chain_ok": data["verify"].get("ok"), "errors": errors,
    }
