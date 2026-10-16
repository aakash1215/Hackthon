"""Headless phone E2E for the PWA (Chromium, 390x844, fake mic + fake GPS), with screenshots.

Flow: onboarding → record → photo/GPS step → saved → process on hub → confirm → ledger → hisaab,
then airplane mode: record offline, reload offline (service worker), reconnect, upload with hash match.

Run from backend/ (needs the hub running):
  PYTHONIOENCODING=utf-8 uv run --no-project python ../scripts/e2e_pwa.py https://localhost:8443 <shots_dir>
"""
import sqlite3
import sys
import time
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "https://localhost:8443"
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else "e2e_shots")
OUT.mkdir(parents=True, exist_ok=True)
DB = Path(__file__).resolve().parents[1] / "data" / "apna.db"


def shot(page, name, full=True):
    page.screenshot(path=str(OUT / f"{name}.png"), full_page=full)
    print("shot", name)


def db_one(sql, args=()):
    con = sqlite3.connect(DB)
    try:
        return con.execute(sql, args).fetchone()
    finally:
        con.close()


def record(page, seconds=4):
    page.get_by_label("रिकॉर्ड शुरू करें").click()
    expect(page.get_by_text("बोलिए… सुन रहे हैं")).to_be_visible()
    time.sleep(seconds)


def sheet_pick(page, row_label, *buttons):
    page.locator(".frow", has_text=row_label).first.click()
    sheet = page.locator(".sheet")
    for b in buttons:
        sheet.get_by_text(b, exact=True).first.click()
    sheet.get_by_role("button", name="यही सही है").click()


with sync_playwright() as p:
    # --ignore-certificate-errors lets the service worker register on the mkcert cert (Chromium here does not trust the CA)
    browser = p.chromium.launch(args=["--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream", "--ignore-certificate-errors"])
    ctx = browser.new_context(
        viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True,
        ignore_https_errors=True, permissions=["microphone", "geolocation"],
        geolocation={"latitude": 19.8762, "longitude": 75.3433, "accuracy": 12}, locale="hi-IN",
    )
    page = ctx.new_page()
    page.on("pageerror", lambda e: print("PAGE ERROR:", e))
    page.goto(BASE)

    # --- onboarding ---------------------------------------------------------------
    expect(page.get_by_text("मज़दूरी का अपना रिकॉर्ड — बस बोलकर")).to_be_visible()
    shot(page, "01_welcome")
    page.get_by_role("button", name="शुरू करें").click()
    shot(page, "02_language")
    page.get_by_role("button", name="आगे बढ़ें").click()
    shot(page, "03_consent")
    page.get_by_role("button", name="मैं सहमत हूँ").click()
    page.get_by_placeholder("नाम लिखें").fill("सुनीता")
    shot(page, "04_category")
    page.get_by_role("button", name="आगे बढ़ें").click()
    page.get_by_placeholder("जैसे: एग्ज़ाम्पल हाइट्स").fill("एग्ज़ाम्पल हाइट्स")
    page.get_by_placeholder("जैसे: बस स्टैंड के पीछे").fill("बस स्टैंड के पीछे")
    page.get_by_role("button", name="पक्का करें").click()
    page.get_by_role("button", name="हाँ, जगह जोड़ें").click()
    expect(page.get_by_text("±12 मी")).to_be_visible()
    shot(page, "05_site")
    page.get_by_role("button", name="आगे बढ़ें").click()
    page.get_by_placeholder("जैसे: कैलाश").fill("कैलाश")
    page.get_by_placeholder("600").fill("600")
    shot(page, "06_contractor")
    page.get_by_role("button", name="हो गया — हिसाब शुरू करें").click()
    expect(page.get_by_text("आज का काम बोलें")).to_be_visible()
    sw = page.evaluate("Promise.race([navigator.serviceWorker.ready.then(() => true), new Promise(r => setTimeout(() => r(false), 15000))])")
    print("service worker ready:", sw)
    time.sleep(2)
    shot(page, "07_home")
    wid = None
    for _ in range(20):
        row = db_one("SELECT id, gps_opt_in FROM workers ORDER BY created_at DESC LIMIT 1")
        site = row and db_one("SELECT zone, zone_confirmed, site_lat FROM sites WHERE worker_id=?", (row[0],))
        if row and site:
            wid = row[0]
            print("worker synced:", row, "site:", site)
            break
        time.sleep(1)
    assert wid, "profile did not sync to the hub"

    # --- record → photo/GPS → saved → process --------------------------------------
    record(page)
    shot(page, "08_record", full=False)
    page.get_by_label("रोकें").click()
    expect(page.get_by_text("फ़ोटो जोड़ें?")).to_be_visible()
    expect(page.locator(".gps-chip", has_text="±")).to_be_visible(timeout=15000)
    shot(page, "09_photo_gps")
    page.get_by_role("button", name="सेव करें").click()
    expect(page.get_by_text("आवाज़ सुरक्षित")).to_be_visible()
    expect(page.get_by_text("कोड मेल खाया")).to_be_visible(timeout=20000)
    shot(page, "10_saved")
    t0 = time.time()
    page.locator("button:has-text('पक्का करें'), :text('अभी समझ नहीं पाए')").first.wait_for(timeout=300000)
    print(f"processing took {time.time() - t0:.0f}s")
    shot(page, "11_saved_processed")
    e = db_one("SELECT id, status, hash_match, lat, audio_sha256 FROM entries WHERE worker_id=? ORDER BY server_ts DESC LIMIT 1", (wid,))
    print("entry:", e)

    # --- confirm ------------------------------------------------------------------
    page.get_by_role("button", name="पक्का करें").click()
    expect(page.get_by_text("पढ़कर सुनाएँ")).to_be_visible(timeout=20000)
    shot(page, "12_confirm")
    sheet_pick(page, "तारीख", "आज")
    sheet_pick(page, "काम शुरू", "सुबह", "9", ":00")
    sheet_pick(page, "काम ख़त्म", "शाम", "7", ":00")
    sheet_pick(page, "आराम (रोज़ का)", "1 घंटा")
    shot(page, "13_confirm_filled")
    page.get_by_role("button", name="सही है").click()
    expect(page.get_by_text("आज का काम बोलें")).to_be_visible(timeout=20000)
    time.sleep(2)
    shot(page, "14_home_after_confirm")
    print("confirmed:", db_one("SELECT status, confirmed FROM entries WHERE id=?", (e[0],)))

    page.get_by_role("button", name="खाता").click()
    time.sleep(2)
    shot(page, "15_ledger")
    page.get_by_role("button", name="हिसाब").click()
    time.sleep(3)
    shot(page, "16_hisaab")

    # --- airplane mode --------------------------------------------------------------
    page.get_by_role("button", name="आज").click()
    ctx.set_offline(True)
    record(page, 3)
    page.get_by_label("रोकें").click()
    expect(page.get_by_text("फ़ोटो जोड़ें?")).to_be_visible()
    page.get_by_role("button", name="सेव करें").click()
    expect(page.get_by_text("हब से जुड़ने पर समझेंगे")).to_be_visible(timeout=20000)
    shot(page, "17_offline_saved")
    page.reload()
    expect(page.get_by_text("आज का काम बोलें")).to_be_visible(timeout=20000)
    expect(page.get_by_text("भेजना बाकी").first).to_be_visible()
    shot(page, "18_offline_reloaded")
    before = db_one("SELECT COUNT(*) FROM entries WHERE worker_id=?", (wid,))[0]
    ctx.set_offline(False)
    page.evaluate("window.dispatchEvent(new Event('online'))")
    for _ in range(40):
        n = db_one("SELECT COUNT(*) FROM entries WHERE worker_id=?", (wid,))[0]
        if n > before:
            break
        time.sleep(1)
    last = db_one("SELECT id, hash_match, client_sha256 = audio_sha256 FROM entries WHERE worker_id=? ORDER BY server_ts DESC LIMIT 1", (wid,))
    print("offline entry uploaded:", last)
    time.sleep(2)
    shot(page, "19_back_online")
    browser.close()
print("E2E OK")
