"""Headless phone E2E for P3 (Chromium 390x844, fake mic + fake GPS) against the running hub, with screenshots.

Flow: onboarding → 3 workdays seeded over the API (real ASR on 1 s clips) → ledger L1/L2 badges →
record thekedar (unskippable notice → Stop → consent choice) → saved → confirm statement → मिलान (diff) →
co-worker confirmation from the ledger → L3 → case file → PDF + bundle.

Run from backend/ (hub running):
  PYTHONIOENCODING=utf-8 .venv/Scripts/python ../scripts/e2e_p3.py https://localhost:8443 <shots_dir>
"""
import io
import re
import json
import ssl
import sqlite3
import sys
import time
import urllib.request
import uuid
import wave
from datetime import date, datetime, timedelta
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "https://localhost:8443"
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else "e2e_p3_shots")
OUT.mkdir(parents=True, exist_ok=True)
DB = Path(__file__).resolve().parents[1] / "data" / "apna.db"
GEO = {"latitude": 19.8762, "longitude": 75.3433, "accuracy": 12}
CTX = ssl.create_default_context()
CTX.check_hostname, CTX.verify_mode = False, ssl.CERT_NONE


def shot(page, name, full=True):
    page.screenshot(path=str(OUT / f"{name}.png"), full_page=full)
    print("shot", name)


def db_one(sql, args=()):
    con = sqlite3.connect(DB)
    try:
        return con.execute(sql, args).fetchone()
    finally:
        con.close()


def api(method, path, body=None, form=None):
    headers, data = {}, None
    if body is not None:
        data, headers = json.dumps(body).encode(), {"Content-Type": "application/json"}
    if form is not None:
        boundary = uuid.uuid4().hex
        parts = []
        for k, v in form.items():
            if isinstance(v, tuple):
                parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"; filename="{v[0]}"\r\n'
                             f'Content-Type: {v[2]}\r\n\r\n'.encode() + v[1] + b"\r\n")
            else:
                parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
        data = b"".join(parts) + f"--{boundary}--\r\n".encode()
        headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
    req = urllib.request.Request(BASE + path, data=data, method=method, headers=headers)
    with urllib.request.urlopen(req, context=CTX, timeout=300) as r:
        return json.loads(r.read())


def silence_wav(seconds=1, salt=b""):
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1), w.setsampwidth(2), w.setframerate(16000)
        w.writeframes(b"\0\0" * 16000 * seconds)
    return buf.getvalue() + salt  # salt keeps each clip's hash distinct


def seed_day(wid, d, gps=False):
    form = {"audio": ("n.wav", silence_wav(salt=d.encode()), "audio/wav"), "kind": "workday", "worker_id": wid,
            "client_ts": f"{d}T19:30:00+05:30"}
    if gps:
        form.update(lat=str(GEO["latitude"]), lon=str(GEO["longitude"]), gps_accuracy_m="12", gps_ts=f"{d}T19:30:00+05:30")
    eid = api("POST", "/api/entries", form=form)["entry_id"]
    api("POST", f"/api/entries/{eid}/process")
    api("POST", f"/api/entries/{eid}/confirm", {"fields": {"work_date": d, "start_time": "09:00", "end_time": "19:00",
                                                           "break_minutes": 60, "worked": "yes"}})


def wait_processed(page, timeout=240):
    expect(page.get_by_role("button", name="पक्का करें")).to_be_visible(timeout=timeout * 1000)


STARTED = datetime.now().astimezone().isoformat(timespec="seconds")

with sync_playwright() as p:
    browser = p.chromium.launch(args=["--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream",
                                      "--ignore-certificate-errors"])
    ctx = browser.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True,
                              has_touch=True, ignore_https_errors=True, permissions=["microphone", "geolocation"],
                              geolocation=GEO, locale="hi-IN")
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: (errors.append(str(e)), print("PAGE ERROR:", e)))
    page.goto(BASE)

    # --- onboarding (same as P2 E2E) ---------------------------------------------------
    page.get_by_role("button", name="शुरू करें").click()
    page.get_by_role("button", name="आगे बढ़ें").click()
    page.get_by_role("button", name="मैं सहमत हूँ").click()
    page.get_by_placeholder("नाम लिखें").fill("सुनीता")
    page.get_by_role("button", name="आगे बढ़ें").click()
    page.get_by_placeholder("जैसे: एग्ज़ाम्पल हाइट्स").fill("एग्ज़ाम्पल हाइट्स")
    page.get_by_placeholder("जैसे: बस स्टैंड के पीछे").fill("बस स्टैंड के पीछे")
    page.get_by_role("button", name="पक्का करें").click()
    page.get_by_role("button", name="हाँ, जगह जोड़ें").click()
    expect(page.get_by_text("±12 मी")).to_be_visible()
    page.get_by_role("button", name="आगे बढ़ें").click()
    page.get_by_placeholder("जैसे: कैलाश").fill("कैलाश")
    page.get_by_placeholder("600").fill("600")
    page.get_by_role("button", name="हो गया — हिसाब शुरू करें").click()
    expect(page.get_by_text("आज का काम बोलें")).to_be_visible()
    wid = None
    for _ in range(20):
        row = db_one("SELECT w.id FROM workers w JOIN sites s ON s.worker_id = w.id "
                     "WHERE s.site_lat IS NOT NULL AND w.created_at >= ? ORDER BY w.created_at DESC LIMIT 1", (STARTED,))
        if row:
            wid = row[0]
            break
        time.sleep(1)
    assert wid, "profile did not sync"
    print("worker", wid)

    # --- seed 3 confirmed days (this month, before today); day 2 has GPS at the site ---------
    today = date.today()
    days = [(today - timedelta(days=n)).isoformat() for n in (3, 2, 1)]
    days = [d for d in days if d[:7] == today.isoformat()[:7]] or [today.isoformat()]
    t0 = time.time()
    for i, d in enumerate(days):
        seed_day(wid, d, gps=(i == 1))
    print(f"seeded {len(days)} days in {time.time() - t0:.0f}s")

    # --- ledger badges -----------------------------------------------------------------------
    page.get_by_role("button", name="खाता").click()
    expect(page.get_by_text("L1 · अपना").first).to_be_visible(timeout=15000)
    if len(days) > 1:
        expect(page.get_by_text("L2 · साइट")).to_be_visible()
    shot(page, "p3_01_ledger_levels")

    # --- record thekedar with the notice -------------------------------------------------------
    page.get_by_role("button", name="आज").click()
    page.get_by_role("button", name="ठेकेदार की बात रिकॉर्ड करें").click()
    expect(page.get_by_text("सूचना किस भाषा में?")).to_be_visible()
    shot(page, "p3_02_notice_lang")
    page.get_by_role("button", name="सूचना सुनाएँ और रिकॉर्ड शुरू करें").click()
    expect(page.get_by_text("पहले सूचना — हर बार, बंद नहीं होती")).to_be_visible()
    assert page.get_by_label("रोकें").count() == 0, "Stop must not exist while the notice plays"
    shot(page, "p3_03_notice_playing", full=False)
    expect(page.get_by_text("रिकॉर्ड हो रहा है")).to_be_visible(timeout=20000)
    time.sleep(3)
    shot(page, "p3_04_recording_thekedar", full=False)
    page.get_by_label("रोकें").click()
    expect(page.get_by_text("ठेकेदार ने हाँ कहा?")).to_be_visible()
    shot(page, "p3_05_consent_choice")
    page.get_by_role("button", name="हाँ — पूरी बातचीत सेव करें").click()
    expect(page.get_by_role("heading", name=re.compile("सुरक्षित"))).to_be_visible()
    t0 = time.time()
    wait_processed(page)
    print(f"thekedar recording processed in {time.time() - t0:.0f}s")
    ent = db_one("SELECT id, notice_played, notice_lang FROM entries WHERE worker_id=? AND speaker='thekedar'", (wid,))
    print("thekedar entry", ent)
    assert ent and ent[1] == 1
    page.get_by_role("button", name="पक्का करें").click()

    # --- confirm the statement: 2 days, ₹600, ₹2000 advance, stance --------------------------------
    def fill(label, value):
        page.locator(".frow", has_text=label).first.click()
        page.locator(".sheet input").fill(str(value))
        page.locator(".sheet").get_by_role("button", name="यही सही है").click()

    expect(page.locator(".frow", has_text="काम के दिन")).to_be_visible(timeout=15000)
    fill("काम के दिन", max(1, len(days) - 1))
    fill("रोज़ की दर", 600)
    fill("उचल / कटौती", 2000)
    page.locator(".frow", has_text="ठेकेदार ने क्या कहा").first.click()
    page.locator(".sheet").get_by_text("दिन नहीं माने").click()
    page.locator(".sheet").get_by_role("button", name="यही सही है").click()
    shot(page, "p3_06_confirm_statement")
    page.get_by_role("button", name="सही है").click()

    # --- मिलान ------------------------------------------------------------------------------------------
    expect(page.get_by_text("फ़र्क़ मिले")).to_be_visible(timeout=30000)
    shot(page, "p3_07_diff")

    # --- co-worker confirmation from the ledger -----------------------------------------------------
    page.goto(BASE)
    page.get_by_role("button", name="खाता").click()
    page.locator(".drow").first.click()
    page.get_by_role("button", name="साथी से पुष्टि कराएँ").click()
    expect(page.get_by_text("किन दिनों साथ काम किया?")).to_be_visible()
    page.get_by_role("button", name="आगे बढ़ें").click()
    shot(page, "p3_08_coworker_prompt", full=False)
    start = page.get_by_role("button", name="साथी राज़ी हैं — रिकॉर्ड शुरू करें")
    expect(start).to_be_enabled(timeout=30000)
    start.click()
    time.sleep(3)
    page.get_by_label("रोकें").click()
    page.get_by_role("button", name="हाँ — पूरी बातचीत सेव करें").click()
    wait_processed(page)
    page.get_by_role("button", name="पक्का करें").click()
    page.locator(".frow", has_text="साथी का नाम").first.click()
    page.locator(".sheet input").fill("रमेश")
    page.locator(".sheet").get_by_role("button", name="यही सही है").click()
    page.get_by_role("checkbox").filter(has_text="हाँ").first.click()
    shot(page, "p3_09_coworker_confirm")
    page.get_by_role("button", name="सही है").click()
    expect(page.get_by_text("L3 · गवाह").first).to_be_visible(timeout=20000)
    shot(page, "p3_10_ledger_l3")

    # --- case file → PDF ---------------------------------------------------------------------------------
    page.get_by_role("button", name="फ़ाइल").click()
    expect(page.get_by_text("तैयार")).to_be_visible(timeout=15000)
    shot(page, "p3_11_case_file")
    page.get_by_role("button", name="PDF बनाएँ").click()
    expect(page.get_by_text("PDF खोलें")).to_be_visible(timeout=120000)
    shot(page, "p3_12_pdf_ready")
    href = page.get_by_text("PDF खोलें").get_attribute("href")
    pdf = urllib.request.urlopen(urllib.request.Request(BASE + href), context=CTX).read()
    print("pdf bytes", len(pdf), pdf[:5])
    assert pdf[:4] == b"%PDF"
    print("chain", api("GET", "/api/chain/verify"))
    print("page errors:", errors or "none")
    browser.close()
