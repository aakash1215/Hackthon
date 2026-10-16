"""सहायक agent: keyword intents, code-filled template answers, no auto-send to the thekedar."""
from datetime import date

import pytest
from fastapi.testclient import TestClient

from app import agent, extract
from app.main import app
from tests.test_entries_api import MR_PAYMENT, MR_WORKDAY, _null, _save, _site, _worker, stub_models  # noqa: F401

client = TestClient(app)


@pytest.mark.parametrize("q,intent", [
    ("मेरा कितना पैसा बाकी है?", "money_due"),
    ("इस हफ़्ते कितने दिन काम किया?", "days_worked"),
    ("अब तक कितने पैसे मिले?", "paid_total"),
    ("मेरी सरकारी मज़दूरी कितनी है?", "min_wage"),
    ("ठेकेदार ने क्या जवाब दिया?", "thekedar_status"),
    ("ठेकेदार को हिसाब भेजो", "send_summary"),
    ("ठेकेदार से लिखित हिसाब माँगो", "ask_written_hisaab"),
    ("पैसा मिला तो कैसे रिकॉर्ड करूँ", "how_record_payment"),
    ("केस फ़ाइल बनानी है", "make_file"),
    ("ठेकेदार ने मारने की धमकी दी", "danger"),
    ("हमारा हिसाब कितना बाकी", "money_due"),  # "मारा" inside "हमारा" is not a threat
    ("आज मौसम कैसा है", "other"),
])
def test_keyword_intents(q, intent):
    assert agent.keyword_intent(q) == intent


def test_periods():
    assert agent.keyword_period("इस हफ़्ते कितने दिन") == "this_week"
    assert agent.keyword_period("पिछले हफ्ते का पैसा") == "last_week"
    assert agent.period_range("this_week", date(2026, 10, 16)) == (date(2026, 10, 12), date(2026, 10, 16))
    assert agent.period_range("last_week", date(2026, 10, 16)) == (date(2026, 10, 5), date(2026, 10, 11))


def test_rupees_indian_grouping():
    assert agent._rupees("363.96") == "₹364"
    assert agent._rupees(123456) == "₹1,23,456"


def test_answers_from_confirmed_record(stub_models):
    _worker()
    _site()
    stub_models["text"] = MR_WORKDAY
    stub_models["llm"] = _null("workday", {})
    eid = _save("workday", client_ts="2026-10-16T10:00:00+05:30").json()["entry_id"]
    client.post(f"/api/entries/{eid}/process")
    client.post(f"/api/entries/{eid}/confirm", json={"fields": {
        "work_date": "2026-10-16", "start_time": "09:00", "end_time": "18:00", "break_minutes": 60, "worked": "yes"}})
    stub_models["text"] = MR_PAYMENT
    stub_models["llm"] = _null("payment", {})
    pid = _save("payment", client_ts="2026-10-16T19:00:00+05:30").json()["entry_id"]
    client.post(f"/api/entries/{pid}/process")
    client.post(f"/api/entries/{pid}/confirm", json={"fields": {"payment_date": "2026-10-16", "amount_paid": 500}})

    r = client.post("/api/agent/ask", json={"worker_id": "w1", "text": "मेरा कितना पैसा बाकी है?"}).json()
    assert r["intent"] == "money_due" and r["source"] == "keywords"
    assert "₹864" in r["text"] and "₹500" in r["text"] and "₹364" in r["text"] and "अनुमान" in r["text"]
    assert r["actions"][0]["screen"] == "hisaab"

    r = client.post("/api/agent/ask", json={"worker_id": "w1", "intent": "paid_total"}).json()
    assert "₹500" in r["text"] and r["source"] == "chip"

    r = client.post("/api/agent/ask", json={"worker_id": "w1", "intent": "days_worked", "period": "all"}).json()
    assert "1 दिन" in r["text"]

    r = client.post("/api/agent/ask", json={"worker_id": "w1", "intent": "min_wage"}).json()
    assert "₹864" in r["text"] and "प्रति दिन" in r["text"]


def test_send_is_only_offered_never_sent(stub_models):
    _worker()
    r = client.post("/api/agent/ask", json={"worker_id": "w1", "text": "ठेकेदार को हिसाब भेजो"}).json()
    assert r["intent"] == "send_summary"
    assert not any(a["type"] == "tg_send" for a in r["actions"])  # not linked → only "connect" is offered
    with agent.db.read() as c:
        assert c.execute("SELECT COUNT(*) FROM tg_messages").fetchone()[0] == 0


def test_unclear_question_uses_llm_as_classifier_only(stub_models, monkeypatch):
    _worker()
    monkeypatch.setattr(extract, "classify", lambda name, msgs, schema, timeout=45, **kw: {
        "intent": "make_file", "period": "all"})
    r = client.post("/api/agent/ask", json={"worker_id": "w1", "text": "मुझे कोर्ट के लिए कागज़ चाहिए"}).json()
    assert r["intent"] == "make_file" and r["source"] == "llm"
    assert r["text"] == agent._STATIC["make_file"][0]  # the answer is the fixed template, not model text


def test_llm_down_degrades_to_help(stub_models, monkeypatch):
    _worker()

    def down(*a, **k):
        raise extract.LLMUnavailable("LLM_ConnectError")

    monkeypatch.setattr(extract, "classify", down)
    r = client.post("/api/agent/ask", json={"worker_id": "w1", "text": "कुछ अलग सवाल पूछना है"}).json()
    assert r["intent"] == "other" and r["source"] == "none" and r["suggestions"]


def test_unknown_worker_and_empty_question():
    assert client.post("/api/agent/ask", json={"worker_id": "nope", "text": "x"}).status_code == 404
    _worker()
    assert client.post("/api/agent/ask", json={"worker_id": "w1", "text": "  "}).status_code == 422
