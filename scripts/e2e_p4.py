"""Headless phone E2E for P4 (Chromium 360x780) against the running hub, with screenshots.

Telegram itself is not needed: after the invite is made in the app, this script links a fake chat and feeds
the thekedar's messages straight into the hub's inbound pipeline (save + hash → real LLM / word guard →
template policy), the same code the bot handlers call. Then it checks the worker's side: Telegram screen
(QR, thread), inbox cards on Home, the S7 promise screen and the S8 stopped screen.

Run from backend/ (hub running):
  PYTHONIOENCODING=utf-8 .venv/Scripts/python ../scripts/e2e_p4.py https://localhost:8443 <shots_dir>
"""
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app import db, telegram_bot as tb  # noqa: E402  (same data/apna.db as the hub)

BASE = sys.argv[1] if len(sys.argv) > 1 else "https://localhost:8443"
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else "e2e_p4_shots")
OUT.mkdir(parents=True, exist_ok=True)
STARTED = datetime.now().astimezone().isoformat(timespec="seconds")
CHAT = 900000 + int(time.time()) % 100000


def shot(page, name, full=True):
    page.screenshot(path=str(OUT / f"{name}.png"), full_page=full)
    print("shot", name)


def inbound(text, mid):
    with db.read() as c:
        link = tb.link_by_chat(c, CHAT)
    row = tb.save_inbound(link, mid, datetime.now(timezone.utc).isoformat(timespec="seconds"), text=text)
    t0 = time.time()
    r = tb.classify_and_act(row["id"])
    print(f"  '{text}' → {r['classification']['intent']} ({time.time() - t0:.0f}s), reply:",
          r["reply"]["text"] if r["reply"] else None)
    return r


with sync_playwright() as p:
    browser = p.chromium.launch(args=["--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream",
                                      "--ignore-certificate-errors"])
    ctx = browser.new_context(viewport={"width": 360, "height": 780}, device_scale_factor=2, is_mobile=True,
                              has_touch=True, ignore_https_errors=True, permissions=["microphone", "geolocation"],
                              geolocation={"latitude": 19.8762, "longitude": 75.3433, "accuracy": 12}, locale="hi-IN")
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: (errors.append(str(e)), print("PAGE ERROR:", e)))
    page.goto(BASE)
    page.get_by_role("button", name="शुरू करें").click()
    page.get_by_role("button", name="आगे बढ़ें").click()
    page.get_by_role("button", name="मैं सहमत हूँ").click()
    page.get_by_placeholder("नाम लिखें").fill("सुनीता")
    page.get_by_role("button", name="आगे बढ़ें").click()
    page.get_by_placeholder("जैसे: एग्ज़ाम्पल हाइट्स").fill("एग्ज़ाम्पल हाइट्स")
    page.get_by_placeholder("जैसे: बस स्टैंड के पीछे").fill("बस स्टैंड के पीछे")
    page.get_by_role("button", name="पक्का करें").click()
    page.get_by_role("button", name="हाँ, जगह जोड़ें").click()
    page.get_by_role("button", name="आगे बढ़ें").click()
    page.get_by_placeholder("जैसे: कैलाश").fill("कैलाश")
    page.get_by_placeholder("600").fill("600")
    page.get_by_role("button", name="हो गया — हिसाब शुरू करें").click()
    expect(page.get_by_text("आज का काम बोलें")).to_be_visible()
    shot(page, "p4_01_home", full=False)
    wid = None
    for _ in range(20):
        with db.read() as c:
            r = c.execute("SELECT id FROM workers WHERE created_at >= ? ORDER BY created_at DESC LIMIT 1",
                          (STARTED,)).fetchone()
        if r:
            wid = r["id"]
            break
        time.sleep(1)
    assert wid
    time.sleep(2)

    # --- Telegram screen: invite + QR --------------------------------------------------------------
    page.goto(BASE)
    page.get_by_text("Telegram").first.click()
    page.get_by_role("button", name="जोड़ने का लिंक बनाएँ").click()
    expect(page.locator("img[src^='data:image/png']")).to_be_visible(timeout=15000)
    shot(page, "p4_02_invite_qr")

    # the thekedar opens the link (simulated: same functions the /start and language handlers call)
    with db.read() as c:
        token = c.execute("SELECT invite_token FROM tg_links WHERE worker_id=? ORDER BY rowid DESC LIMIT 1",
                          (wid,)).fetchone()[0]
    assert tb.start_link(token, CHAT, 4242, "kailas_demo")
    assert tb.choose_lang(CHAT, "hi")
    expect(page.get_by_text("जुड़े हैं")).to_be_visible(timeout=15000)
    inbound("Somvaar ko 5000 dunga", 11)
    inbound("अभी पैसा नहीं है", 12)
    inbound("saale, phir paisa maanga to haath pair tod dunga", 13)
    page.reload()
    page.wait_for_timeout(2500)
    shot(page, "p4_03_linked_thread")

    # --- Home inbox cards → promise (S7) → stopped (S8) ---------------------------------------------
    page.goto(BASE)
    expect(page.get_by_text("वादा किया").first).to_be_visible(timeout=25000)
    shot(page, "p4_04_home_inbox")
    page.get_by_text("वादा किया").first.click()
    expect(page.get_by_text("जवाब में वादा मिला")).to_be_visible()
    shot(page, "p4_05_promise")
    page.get_by_role("button", name="सही है, सेव करें").click()
    page.wait_for_timeout(800)
    sheet = page.locator(".sheet")
    if sheet.count():
        sheet.locator(".option", has_text="से मेल").first.click()  # the day matching his words; a tap confirms it
        page.get_by_role("button", name="सही है, सेव करें").click()
    page.wait_for_timeout(1500)
    with db.read() as c:
        pr = c.execute("SELECT amount, due_date, source FROM promises WHERE worker_id=?", (wid,)).fetchone()
    print("promise saved:", dict(pr) if pr else None)
    assert pr and pr["amount"] == 5000 and pr["source"] == "telegram"
    page.goto(BASE)
    page.get_by_text("बातचीत रोक दी गई").first.click()
    expect(page.get_by_text("ऐप ने कोई जवाब नहीं दिया")).to_be_visible()
    shot(page, "p4_06_stopped")
    with db.read() as c:
        link = tb.link_by_chat(c, CHAT)
        outs = [dict(r) for r in c.execute("SELECT template_id, status FROM tg_messages WHERE chat_id=? AND direction='out'",
                                           (CHAT,))]
    print("paused:", link["paused"], "outbound:", outs)
    assert link["paused"] == 1 and [o["template_id"] for o in outs] == ["INTRO", "NOTED_PROMISE", "NOTED"]
    # the chat id is made up: never let the live bot send these replies to a real Telegram user
    with db.write() as c:
        c.execute("UPDATE tg_messages SET status='failed', classification='{\"error\":\"E2E_FAKE_CHAT\"}' "
                  "WHERE chat_id=? AND direction='out' AND status='pending'", (CHAT,))
        c.execute("UPDATE tg_links SET paused=1 WHERE chat_id=?", (CHAT,))
    print("page errors:", errors or "none")
    browser.close()
