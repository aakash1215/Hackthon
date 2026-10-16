"""Telegram thekedar agent (BUILD_PLAN §7, AC24): linking, template-only outbox, reply policy, hostile stop.
No network: the LLM classifier is stubbed per message and Telegram is replaced by a fake bot."""
import asyncio
import dataclasses
import json
from datetime import datetime, timezone

import pytest

from app import db, extract, telegram_bot as tb
from app.tg_policy import TEMPLATES, decide, hostile_guard, render
from tests.test_entries_api import client, stub_models  # noqa: F401
from tests.test_p3_api import _day, _setup

NOW = datetime.now(timezone.utc).isoformat(timespec="seconds")


def _f(v=None, ev=None):
    return {"value": v, "evidence": ev}


# What the (stubbed) open-weight classifier returns for each scripted message.
SCRIPT = {
    "Somvaar ko 5000 dunga": {"intent": "promise_to_pay", "confidence": "high", "amount": _f(5000, "5000"),
                              "date": _f("Somvaar", "Somvaar"), "days": _f()},
    "abhi paisa nahi hai": {"intent": "refuses", "confidence": "high", "amount": _f(), "date": _f(), "days": _f()},
    # the classifier misses the threat; the deterministic word guard must still catch it
    "saale, phir paisa maanga to haath pair tod dunga": {"intent": "other", "confidence": "low", "amount": _f(),
                                                         "date": _f(), "days": _f()},
    "kitne din ka hisaab hai?": {"intent": "asks_details", "confidence": "high", "amount": _f(), "date": _f(),
                                 "days": _f()},
    "maine 2000 de diye the": {"intent": "partial_payment_claim", "confidence": "high", "amount": _f(2000, "2000"),
                               "date": _f(), "days": _f()},
    "12 din hi kaam kiya": {"intent": "disputes_days", "confidence": "high", "amount": _f(), "date": _f(),
                            "days": _f(12, "12 din")},
}


@pytest.fixture
def linked(stub_models, monkeypatch):
    monkeypatch.setattr(tb, "settings", dataclasses.replace(tb.settings, telegram_bot_token="TEST",
                                                            telegram_bot_username="test_bot"))
    monkeypatch.setattr(extract, "extract_reply", lambda text, timeout=300: SCRIPT[text])
    stub_models["llm"] = None
    _setup()
    for d in ("2026-10-01", "2026-10-02", "2026-10-03"):
        _day(d)
    inv = client.post("/api/telegram/invite", json={"worker_id": "w1"}).json()
    assert inv["invite_url"].startswith("https://t.me/test_bot?start=") and inv["qr_png"].startswith("data:image/png")
    assert tb.start_link(inv["token"], 555, 777, "kailas") is not None
    assert tb.choose_lang(555, "hi") is not None
    return inv


def _out():
    with db.read() as c:
        return [dict(r) for r in c.execute("SELECT * FROM tg_messages WHERE direction='out' ORDER BY created_at, rowid")]


def _types():
    with db.read() as c:
        return [r["type"] for r in c.execute("SELECT type FROM events ORDER BY seq")]


def _inbound(text, mid=1):
    with db.read() as c:
        link = tb.link_by_chat(c, 555)
    row = tb.save_inbound(link, mid, NOW, text=text)
    return tb.classify_and_act(row["id"])


def _inbox():
    return client.get("/api/inbox", params={"worker_id": "w1"}).json()["items"]


# --- pure policy -------------------------------------------------------------------------------

def test_hostile_guard_words_and_no_false_alarms():
    assert hostile_guard("तुझे देख लूँगा")
    assert hostile_guard("Saale paisa nahi milega")
    assert hostile_guard("हाकलून देईन तुला")
    assert hostile_guard("हाथ पैर तोड़ दूँगा")
    for ok in ("salary kab milegi", "for sale", "Somvaar ko 5000 dunga", "हिसाब ठीक है", "हो बरोबर आहे"):
        assert hostile_guard(ok) is None, ok


def test_decide_table():
    assert decide("promise_to_pay", "high", amount=5000, date_text="Somvaar").template_id == "NOTED_PROMISE"
    assert decide("promise_to_pay", "high", amount=5000).template_id == "NOTED_ASK_DATE"
    assert decide("acknowledges", "high").inbox_kind == "message"
    assert decide("asks_details", "high") == decide("asks_details", "high")
    assert decide("promise_to_pay", "low", amount=5000).template_id is None  # low confidence → no reply
    assert decide(None, None).template_id is None  # LLM down → log + alert, no reply
    h = decide("acknowledges", "high", guard_hit="तोड़ दूँगा")
    assert h.template_id is None and h.pause and h.inbox_kind == "hostile"


def test_templates_never_mention_law_or_threats():
    banned = ("धारा", "section", "court", "कोर्ट", "न्यायालय", "penalty", "जुर्माना", "पुलिस", "police", "केस")
    for tid, langs in TEMPLATES.items():
        for lang, text in langs.items():
            assert not any(b.lower() in text.lower() for b in banned), (tid, lang)


# --- linking -------------------------------------------------------------------------------------

def test_link_language_then_intro_first(linked):
    out = _out()
    assert [m["template_id"] for m in out] == ["INTRO"]  # LANG_ASK is sent by the handler on /start
    assert out[0]["text"].startswith("नमस्ते, मैं") and "सुरक्षित रखे जाते हैं" in out[0]["text"]
    assert "TG_LINKED" in _types()
    assert tb.choose_lang(555, "mr") is None  # second tap changes nothing
    assert tb.start_link("not-a-token", 999, 1, "x") is None  # unknown invite: silent
    assert tb.start_link(linked["token"], 999, 1, "x") is None  # someone else can't take the link
    st = client.get("/api/telegram/status", params={"worker_id": "w1"}).json()
    assert st["link"]["linked"] and st["link"]["tg_username"] == "kailas" and st["link"]["lang"] == "hi"


# --- the 6 scripted messages (BUILD_PLAN §7 pytest) -------------------------------------------------

def test_promise_somvaar_5000(linked):
    r = _inbound("Somvaar ko 5000 dunga")
    assert r["decision"].template_id == "NOTED_PROMISE"
    assert r["reply"]["text"] == "नोट कर लिया: ₹5,000, Somvaar। धन्यवाद।"
    item = _inbox()[0]
    assert item["kind"] == "promise" and item["amount"] == 5000 and item["date_text"] == "Somvaar"
    assert item["thekedar_name"] == "Kailas"
    # the promise counts only after the worker confirms it
    led = client.get("/api/ledger", params={"worker_id": "w1"}).json()
    assert all(d["corroboration"]["level"] == 1 for d in led["days"])  # not yet: the worker hasn't confirmed
    bad = client.post(f"/api/inbox/{item['id']}", json={"action": "confirm"})
    assert bad.json()["detail"] == "AMOUNT_REQUIRED"
    ok = client.post(f"/api/inbox/{item['id']}", json={"action": "confirm", "amount": 5000,
                                                       "due_date": "2026-10-19", "remind": True}).json()
    assert ok["status"] == "confirmed" and ok["promise_id"]
    assert "PROMISE_LOGGED" in _types()
    p = client.get("/api/promises", params={"worker_id": "w1"}).json()["items"][0]
    assert p["source"] == "telegram" and p["amount"] == 5000 and p["reminder_at"] == "2026-10-19T09:00:00"
    led = client.get("/api/ledger", params={"worker_id": "w1"}).json()
    same_month = [d for d in led["days"] if d["date"][:7] == NOW[:7]]
    assert same_month and all(d["corroboration"]["level"] == 3 for d in same_month)


def test_refuses(linked):
    r = _inbound("abhi paisa nahi hai")
    assert r["reply"]["template_id"] == "NOTED" and r["reply"]["text"] == "नोट कर लिया। धन्यवाद।"
    assert _inbox()[0]["kind"] == "refuses"


def test_abusive_line_no_reply_pause_and_alert(linked):
    n_before = len(_out())
    r = _inbound("saale, phir paisa maanga to haath pair tod dunga")
    assert r["decision"].template_id is None and r["reply"] is None
    assert len(_out()) == n_before  # nothing was sent back
    assert r["classification"]["guard"]
    assert "TG_HOSTILE_STOP" in _types()
    assert _inbox()[0]["kind"] == "hostile"
    st = client.get("/api/telegram/status", params={"worker_id": "w1"}).json()
    assert st["link"]["paused"] is True
    # automatic and worker-triggered messages stop too
    _day("2026-10-04")
    assert len(_out()) == n_before
    assert client.post("/api/telegram/send", json={"worker_id": "w1", "template": "SUMMARY"}).json()["detail"] == "PAUSED"


def test_asks_details_gets_summary_from_ledger(linked):
    r = _inbound("kitne din ka hisaab hai?")
    assert r["reply"]["template_id"] == "SUMMARY"
    assert "कुल दिन: 3" in r["reply"]["text"] and "09:00–19:00" in r["reply"]["text"]
    assert "(अनुमान)" in r["reply"]["text"]
    assert _inbox() == []


def test_partial_payment_claim_needs_worker(linked):
    r = _inbound("maine 2000 de diye the")
    assert r["reply"]["text"] == "नोट कर लिया। Sunita इसकी पुष्टि करेंगे।"
    item = _inbox()[0]
    assert item["kind"] == "partial_payment" and item["amount"] == 2000
    assert client.post(f"/api/inbox/{item['id']}", json={"action": "deny"}).json()["status"] == "denied"
    assert "TG_CLAIM_DENIED" in _types()


def test_dispute_quotes_ledger_days_and_flags_days(linked):
    r = _inbound("12 din hi kaam kiya")
    month = sum(1 for d in client.get("/api/ledger", params={"worker_id": "w1"}).json()["days"]
                if d["date"][:7] == datetime.now().astimezone().date().isoformat()[:7])
    assert r["reply"]["text"] == f"नोट कर लिया। Sunita के रिकॉर्ड में {month} दिन दर्ज हैं। कृपया अपना लिखित हिसाब भेजें।"
    assert _inbox()[0]["kind"] == "dispute"


# --- outbox ------------------------------------------------------------------------------------------

def test_confirm_sends_daily_update_and_payment_ack_from_templates(linked):
    _day(datetime.now().astimezone().date().isoformat())
    out = _out()
    assert out[-1]["template_id"] == "DAILY_UPDATE" and out[-1]["status"] == "pending"
    assert out[-1]["text"].startswith("आज ") and "09:00–19:00" in out[-1]["text"] and "बाकी (अनुमान): ₹" in out[-1]["text"]
    client.post("/api/telegram/settings", json={"worker_id": "w1", "auto_daily": False})
    _day("2026-10-05")
    assert _out()[-1]["template_id"] == "DAILY_UPDATE"  # nothing new while auto_daily is off
    assert all(m["template_id"] for m in _out())  # every outbound message is a template


def test_daily_limit_five(linked):
    for _ in range(4):  # INTRO + 4 = 5
        assert client.post("/api/telegram/send", json={"worker_id": "w1", "template": "REQUEST_WRITTEN_HISAAB"}).status_code == 200
    r = client.post("/api/telegram/send", json={"worker_id": "w1", "template": "SUMMARY"})
    assert r.status_code == 429 and r.json()["detail"] == "DAILY_LIMIT"
    assert "TG_RATE_LIMITED" in _types()


def test_llm_down_logs_and_alerts_without_reply(linked, monkeypatch):
    def down(text, timeout=300):
        raise extract.LLMUnavailable("LLM_ConnectError")

    monkeypatch.setattr(extract, "extract_reply", down)
    r = _inbound("Somvaar ko 5000 dunga")
    assert r["reply"] is None and _inbox()[0]["kind"] == "message"
    assert r["classification"]["llm_error"] == "LLM_ConnectError"


def test_flush_marks_sent_with_telegram_time_and_hash(linked):
    class Sent:
        def __init__(self, i):
            self.message_id, self.date = i, datetime(2026, 10, 16, 8, 0, tzinfo=timezone.utc)

    class FakeBot:
        def __init__(self):
            self.sent = []

        async def send_message(self, chat_id, text, reply_markup=None):
            self.sent.append((chat_id, text))
            return Sent(len(self.sent))

    rt = tb.Runtime()
    rt.app, rt.running = type("A", (), {"bot": FakeBot()})(), True
    asyncio.run(rt.flush())
    m = _out()[0]
    assert m["status"] == "sent" and m["tg_date"] == "2026-10-16T08:00:00+00:00" and len(m["sha256"]) == 64
    assert rt.app.bot.sent[0][0] == 555
    assert "TG_MESSAGE_OUT" in _types()
    msgs = client.get("/api/telegram/messages", params={"worker_id": "w1"}).json()["items"]
    assert msgs[0]["direction"] == "out" and msgs[0]["status"] == "sent"


def test_inbound_saved_with_telegram_timestamp_and_in_packet(linked, monkeypatch):
    from app import packet

    monkeypatch.setattr(packet, "_render_pdf", lambda h, p: "PDF_UNAVAILABLE:test")
    _inbound("Somvaar ko 5000 dunga", mid=42)
    with db.read() as c:
        m = dict(c.execute("SELECT * FROM tg_messages WHERE direction='in'").fetchone())
    assert m["tg_date"] == NOW and m["tg_message_id"] == 42 and len(m["sha256"]) == 64
    assert json.loads(m["classification"])["intent"] == "promise_to_pay"
    assert "TG_MESSAGE_IN" in _types()
    out = client.post("/api/export", json={"worker_id": "w1", "date_from": NOW[:8] + "01", "date_to": NOW[:10]}).json()
    html = client.get(out["html_url"]).text
    assert "Somvaar ko 5000 dunga" in html and "promise to pay" in html


def test_render_fills_missing_with_dash():
    assert render("NOTED_PROMISE", "hi", amount="5,000", date=None) == "नोट कर लिया: ₹5,000, —। धन्यवाद।"
