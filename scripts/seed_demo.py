"""Seed the synthetic demo persona "सुनीता (डेमो)" into data/demo/ (BUILD_PLAN P6). SYNTHETIC DEMO DATA only.

Usage (repo root):  backend/.venv/Scripts/python scripts/seed_demo.py [--reset]

Everything goes through the real API in-process (FastAPI TestClient, lifespan NOT entered, so the
Telegram bot never starts). Only ASR and the LLM are replaced by scripted outputs, exactly like the
tests do; every number still flows through the normalizer, reconciler, confirm step and wage engine.
All files are generated here (tones, drawn images) and carry "SYNTHETIC DEMO DATA". No real people.
"""
from __future__ import annotations

import argparse
import dataclasses
import hashlib
import io
import math
import os
import shutil
import struct
import sys
import wave
from datetime import date, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DEMO_DIR = REPO / "data" / "demo"
WID = "demo-sunita"
SITE_PT = (18.5204, 73.8567)
MONTH_FROM, MONTH_TO = "2026-10-01", "2026-10-31"
DAYS = [date(2026, 10, d).isoformat() for d in range(1, 14)]  # 13 workdays, 01..13 Oct
GPS_DAYS = {2, 5, 9, 11}  # day-of-month with an on-site GPS fix → L2
PHOTO_DAY = 4  # site photo (+ site board photo) → L2
COWORKER_DATES = DAYS[:7]  # 01..07 Oct → L3
PAYMENTS = [("2026-10-06", 2000, "आज कैलाश ठेकेदाराने दोन हजार रुपये रोख दिले.", "दोन हजार रुपये"),
            ("2026-10-13", 2500, "आज ठेकेदाराकडून अडीच हजार रुपये रोख मिळाले.", "अडीच हजार रुपये")]

# Three synthetic Marathi phrasings of "09:00 to 19:00, one hour lunch", with the exact evidence spans.
WORKDAY_TEXTS = [
    ("सकाळी नऊ ते संध्याकाळी सात काम केलं, एक तास जेवण.",
     {"start_time": "सकाळी नऊ", "end_time": "संध्याकाळी सात", "break_minutes": "एक तास जेवण", "worked": "काम केलं"}),
    ("आज सकाळी नऊ वाजता आले, संध्याकाळी सात वाजता सुटले. जेवणाला एक तास.",
     {"start_time": "सकाळी नऊ वाजता", "end_time": "संध्याकाळी सात वाजता", "break_minutes": "जेवणाला एक तास"}),
    ("नऊ ते सात साइटवर काम केलं, दुपारी एक तास सुट्टी.",
     {"start_time": "नऊ", "end_time": "सात", "break_minutes": "एक तास सुट्टी", "worked": "काम केलं"}),
]
WORKDAY_VALUES = {"start_time": "09:00", "end_time": "19:00", "break_minutes": 60, "worked": "yes"}

THEKEDAR_TEXT = "बारा दिवस, सहाशे रोज, दोन हजार उचल कापली, बाकी सोमवारी देतो"
COWORKER_TEXT = "माझं नाव रमेश. मी रेकॉर्डिंगला तयार आहे. सुनीता एक ते सात तारखेपर्यंत माझ्यासोबत कामावर होती."
TG_DISPUTE = "13 नहीं, 12 दिन ही काम किया"
TG_PROMISE = "Somvaar ko 5000 dunga"


# --- synthetic files ---------------------------------------------------------------------------------

def tone_wav(seed: int, seconds: float = 1.2) -> bytes:
    """A short 16 kHz mono tone; frequency varies with the seed so every file hashes differently."""
    rate, f = 16000, 220 + 17 * seed
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        frames = b"".join(struct.pack("<h", int(6000 * math.sin(2 * math.pi * f * i / rate)))
                          for i in range(int(rate * seconds)))
        w.writeframes(frames)
    return buf.getvalue()


def _font(size: int):
    from PIL import ImageFont

    for name in ("Nirmala.ttf", "arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default(size=size)


def _watermark(img):
    """Big diagonal + banner "SYNTHETIC DEMO DATA" (always visible)."""
    from PIL import Image, ImageDraw

    w, h = img.size
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f = _font(int(w / 11))
    text = "SYNTHETIC DEMO DATA"
    tw = d.textlength(text, font=f)
    d.text(((w - tw) / 2, h / 2 - w / 22), text, font=f, fill=(200, 20, 20, 110))
    layer = layer.rotate(28, center=(w / 2, h / 2))
    img = Image.alpha_composite(img.convert("RGBA"), layer)
    d = ImageDraw.Draw(img)
    d.rectangle([0, h - 44, w, h], fill=(200, 20, 20, 255))
    fb = _font(24)
    d.text((14, h - 37), "SYNTHETIC DEMO DATA · not a real person or site", font=fb, fill=(255, 255, 255, 255))
    return img.convert("RGB")


def _jpeg(img) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


def site_photo(day: str) -> bytes:
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (720, 960), (150, 196, 230))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 640, 720, 960], fill=(160, 130, 95))  # ground
    d.rectangle([140, 220, 560, 660], fill=(205, 200, 190))  # building
    for y in range(240, 640, 70):  # slabs + window gaps
        d.rectangle([140, y, 560, y + 10], fill=(120, 120, 120))
        for x in range(170, 540, 90):
            d.rectangle([x, y + 22, x + 50, y + 58], fill=(70, 70, 80))
    for x in range(120, 600, 60):  # scaffolding
        d.line([x, 200, x, 660], fill=(110, 80, 40), width=5)
    for y in range(200, 660, 55):
        d.line([120, y, 580, y], fill=(110, 80, 40), width=4)
    d.rectangle([0, 0, 720, 70], fill=(255, 255, 255))
    d.text((16, 16), f"Example Heights, Wing B · site photo · {day}", font=_font(26), fill=(30, 30, 30))
    return _jpeg(_watermark(img))


def site_board_photo() -> bytes:
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (960, 640), (90, 120, 90))
    d = ImageDraw.Draw(img)
    d.rectangle([60, 60, 900, 520], fill=(250, 250, 240), outline=(20, 60, 140), width=10)
    lines = [("Example Heights, Wing B", 44), ("Developer: Example Developers", 34),
             ("MahaRERA P52100000000", 34), ("Pune, Maharashtra", 30), ("SYNTHETIC", 34)]
    y = 100
    for t, s in lines:
        d.text((100, y), t, font=_font(s), fill=(20, 40, 110))
        y += s + 34
    return _jpeg(_watermark(img))


def cash_slip(day: str, amount: int) -> bytes:
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (640, 860), (238, 236, 228))
    d = ImageDraw.Draw(img)
    d.rectangle([40, 60, 600, 720], fill=(255, 255, 255), outline=(150, 150, 150), width=3)
    rows = [("Cash payment slip", 38), (f"₹{amount:,} · SYNTHETIC", 52), (f"Date: {day}", 30),
            ("Paid by: Kailas (demo)", 30), ("To: Sunita (demo)", 30), ("Mode: cash", 30)]
    y = 110
    for t, s in rows:
        d.text((80, y), t, font=_font(s), fill=(30, 30, 30))
        y += s + 40
    return _jpeg(_watermark(img))


# --- seeding ---------------------------------------------------------------------------------------------

def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _f(v=None, ev=None):
    return {"value": v, "evidence": ev}


def main() -> int:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")  # Devanagari in the summary on a cp1252 Windows console
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--reset", action="store_true", help="delete data/demo/ first")
    args = ap.parse_args()
    if (DEMO_DIR / "apna.db").exists():
        if not args.reset:
            print(f"{DEMO_DIR / 'apna.db'} exists. Run with --reset to rebuild it.", file=sys.stderr)
            return 2
        assert DEMO_DIR.resolve() == (REPO / "data" / "demo").resolve()  # never anything else
        shutil.rmtree(DEMO_DIR)
    DEMO_DIR.mkdir(parents=True, exist_ok=True)

    os.environ["DATA_DIR"] = str(DEMO_DIR)  # before app.config is imported (env wins over .env)
    sys.path.insert(0, str(REPO / "backend"))
    from fastapi.testclient import TestClient

    from app import asr, db, extract, telegram_bot as tb
    from app.contracts import KIND_FIELDS
    from app.main import app

    assert db.settings.data_dir.resolve() == DEMO_DIR.resolve(), db.settings.data_dir
    db.init_db()
    client = TestClient(app)  # no `with`: the lifespan (and the Telegram bot) never starts

    # --- scripted "models" (ASR + LLM); everything else is the real pipeline ---------------------------
    state: dict = {"text": "", "llm": None, "reply": None}

    def fake_wav(src, dst):
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)  # the synthetic WAV is already 16 kHz mono
        return dst

    def fake_asr(wav, language):
        t = state["text"]
        return {"language": "mr" if language == "auto" else language, "duration": 6.0, "text": t,
                "segments": [{"start": 0, "end": 6.0, "text": t, "avg_logprob": -0.25, "no_speech_prob": 0.01,
                              "words": []}]}

    def fake_extract(kind, transcript, rec_date, context=None, timeout=300):
        out = {n: _f() for n in KIND_FIELDS[kind]}
        out.update(state["llm"] or {})
        return out

    asr.to_wav16k, asr.transcribe_wav, extract.extract = fake_wav, fake_asr, fake_extract
    extract.extract_reply = lambda text, timeout=300: state["reply"]

    def ok(r, what):
        assert r.status_code == 200, f"{what}: {r.status_code} {r.text}"
        return r.json()

    def record(kind, audio, text, llm, ts, **form):
        state.update(text=text, llm=llm)
        r = ok(client.post("/api/entries", files={k: v for k, v in form.pop("_files", {}).items()} | {
            "audio": ("note.wav", audio, "audio/wav")},
            data={"kind": kind, "worker_id": WID, "client_ts": ts, "client_sha256": _sha(audio), **form}), "save")
        p = ok(client.post(f"/api/entries/{r['entry_id']}/process"), "process")
        assert p["status"] == "processed", p
        return r["entry_id"]

    def confirm(eid, fields):
        return ok(client.post(f"/api/entries/{eid}/confirm", json={"fields": fields}), "confirm")

    # --- profile ----------------------------------------------------------------------------------------
    ok(client.post("/api/workers", json={"id": WID, "display_name": "सुनीता (डेमो)", "language": "mr",
                                          "category": "unskilled", "default_break_min": 60,
                                          "consent_keep_audio": True, "gps_opt_in": True}), "worker")
    ok(client.post("/api/sites", json={
        "worker_id": WID, "name": "Example Heights, Wing B", "landmark": "SYNTHETIC demo site", "city": "पुणे",
        "state": "Maharashtra", "sphere": "state", "zone": "I", "zone_confirmed": True, "employment_sn": 11,
        "wage_period": "monthly", "site_lat": SITE_PT[0], "site_lon": SITE_PT[1], "site_gps_accuracy_m": 10}), "site")
    ok(client.post("/api/parties", json={"worker_id": WID, "role": "contractor", "name": "कैलाश (डेमो)",
                                          "phone": "90000 00000", "source": "stated"}), "party")

    # --- 13 workdays -----------------------------------------------------------------------------------
    for i, day in enumerate(DAYS):
        n = int(day[-2:])
        text, spans = WORKDAY_TEXTS[i % len(WORKDAY_TEXTS)]
        llm = {k: _f(WORKDAY_VALUES[k], ev) for k, ev in spans.items()}
        gps = {}
        if n in GPS_DAYS:
            gps = {"lat": str(SITE_PT[0] + 0.0003 * (n % 3)), "lon": str(SITE_PT[1] + 0.0002),
                   "gps_accuracy_m": "12", "gps_ts": f"{day}T19:25:00+05:30"}
        eid = record("workday", tone_wav(n), text, llm, f"{day}T19:30:00+05:30", **gps)
        confirm(eid, {"work_date": day, **WORKDAY_VALUES})
        if n == PHOTO_DAY:
            for kind, img, ts in (("photo", site_photo(day), f"{day}T11:05:00+05:30"),
                                  ("site_board", site_board_photo(), f"{day}T11:07:00+05:30")):
                r = ok(client.post("/api/evidence/photo", files={"photo": (f"{kind}.jpg", img, "image/jpeg")},
                                   data={"worker_id": WID, "kind": kind, "client_ts": ts, "client_sha256": _sha(img),
                                         "lat": str(SITE_PT[0] + 0.0002), "lon": str(SITE_PT[1]),
                                         "gps_accuracy_m": "15",
                                         "caption": "SYNTHETIC DEMO DATA"}), kind)
                assert r["hash_match"] is True
            ok(client.post("/api/sites/board", json={"worker_id": WID, "principal_employer": "Example Developers",
                                                      "maharera_no": "P52100000000"}), "board")

        # payments land on their own day, right after that day's note
        for pday, amount, ptext, pspan in PAYMENTS:
            if pday != day:
                continue
            slip = cash_slip(pday, amount)
            llm = {"amount_paid": _f(amount, pspan), "payment_mode": _f("cash", "रोख")}
            if "कैलाश" in ptext:
                llm["payer_name"] = _f("कैलाश", "कैलाश")
            pid = record("payment", tone_wav(40 + n), ptext, llm, f"{pday}T19:40:00+05:30",
                         _files={"photo": ("slip.jpg", slip, "image/jpeg")}, photo_client_sha256=_sha(slip))
            confirm(pid, {"payment_date": pday, "amount_paid": amount, "payment_mode": "cash",
                          "payer_name": "कैलाश (डेमो)"})

    # --- consented co-worker confirmation (01..07 Oct → L3) ---------------------------------------------
    cw = record("coworker_confirm", tone_wav(70), COWORKER_TEXT,
                {"coworker_name": _f("रमेश", "रमेश"), "consent_phrase": _f("मी रेकॉर्डिंगला तयार आहे",
                                                                          "मी रेकॉर्डिंगला तयार आहे"),
                 "dates_or_days": _f("एक ते सात तारखेपर्यंत", "एक ते सात तारखेपर्यंत")},
                "2026-10-07T19:50:00+05:30", speaker="coworker", notice_played="true")
    confirm(cw, {"coworker_name": "रमेश (डेमो)", "consent": True, "dates": COWORKER_DATES})

    # --- consented thekedar recording → differences ---------------------------------------------------------
    state["reply"] = {"intent": "disputes_days", "confidence": "high", "amount": _f(), "date": _f("सोमवारी", "सोमवारी"),
                      "days": _f(12, "बारा दिवस")}
    tk = record("hisaab_statement", tone_wav(80), THEKEDAR_TEXT,
                {"days_counted": _f(12, "बारा दिवस"), "rate_per_day": _f(600, "सहाशे रोज"),
                 "deductions": _f(2000, "दोन हजार उचल कापली"), "promised_date": _f("सोमवारी", "सोमवारी")},
                "2026-10-14T18:00:00+05:30", speaker="thekedar", notice_played="true", notice_lang="hi")
    confirm(tk, {"days_counted": 12, "rate_per_day": 600, "deductions": 2000, "intent": "disputes_days"})
    diff = ok(client.get(f"/api/entries/{tk}/differences"), "differences")
    codes = [i["code"] for i in diff["items"]]
    assert codes == ["DAYS_DIFF", "RATE_BELOW_MIN", "OT_NOT_COUNTED", "DEDUCTION_DISPUTED"], codes

    # --- Telegram thread (fake chat -1: never a real person; nothing left pending) -----------------------
    tb.settings = dataclasses.replace(tb.settings, telegram_bot_token="DEMO",
                                      telegram_bot_username=tb.settings.telegram_bot_username or "apna_hisaab_bot")
    inv = ok(client.post("/api/telegram/invite", json={"worker_id": WID}), "invite")
    assert tb.start_link(inv["token"], -1, 1, "kailas_demo") is not None
    assert tb.choose_lang(-1, "hi") is not None
    tg_id = iter(range(100, 200))

    def flush(tg_date: str):
        for m in tb.pending_out():
            assert m["chat_id"] == -1, m
            tb.mark_sent(m["id"], next(tg_id), tg_date)

    flush("2026-10-14T12:50:00+00:00")  # INTRO
    script = [(TG_DISPUTE, "2026-10-14T13:10:00+00:00", "2026-10-14T13:10:40+00:00",
               {"intent": "disputes_days", "confidence": "high", "amount": _f(), "date": _f(),
                "days": _f(12, "12 दिन")}),
              (TG_PROMISE, "2026-10-15T05:00:00+00:00", "2026-10-15T05:00:35+00:00",
               {"intent": "promise_to_pay", "confidence": "high", "amount": _f(5000, "5000"),
                "date": _f("Somvaar", "Somvaar"), "days": _f()})]
    with db.read() as c:
        link = tb.link_by_chat(c, -1)
    for text, t_in, t_out, reply in script:
        state["reply"] = reply
        row = tb.save_inbound(link, next(tg_id), t_in, text=text)
        res = tb.classify_and_act(row["id"])
        assert res["reply"], res
        flush(t_out)
    ok(client.post("/api/telegram/settings", json={"worker_id": WID, "auto_daily": False}), "tg settings")
    with db.read() as c:
        pending = c.execute("SELECT COUNT(*) FROM tg_messages WHERE status='pending'").fetchone()[0]
    assert pending == 0, "demo outbox must be empty so the live bot never sends demo messages"

    # --- summary ------------------------------------------------------------------------------------------
    h = ok(client.get("/api/hisaab", params={"worker_id": WID, "date_from": MONTH_FROM, "date_to": MONTH_TO}), "hisaab")
    led = ok(client.get("/api/ledger", params={"worker_id": WID}), "ledger")
    levels = {n: sum(1 for d in led["days"] if d["corroboration"]["level"] == n) for n in (1, 2, 3)}
    chain = ok(client.get("/api/chain/verify"), "chain")
    inbox = ok(client.get("/api/inbox", params={"worker_id": WID}), "inbox")["items"]
    print("SYNTHETIC DEMO DATA seeded into", DEMO_DIR)
    print("  days:", len(led["days"]), "payments:", [p["amount"] for p in led["payments"]],
          "proof photos:", sum(p["proof_photos"] for p in led["payments"]))
    print("  hisaab totals:", h.get("totals") if h.get("ok") else h.get("errors"))
    print("  levels:", " ".join(f"L{n}={levels[n]}" for n in (1, 2, 3)))
    print("  differences:", codes, "thekedar_total:", diff.get("thekedar_total"), "record_total:", diff.get("record_total"))
    print("  inbox:", [(i["kind"], i["status"]) for i in inbox])
    print("  chain:", chain)
    print("  phone: https://<LAN-IP>:8443/?demo=" + WID + "  (hub started with DATA_DIR=data/demo)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
