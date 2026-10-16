"""TG_AGENT=chatgpt: the agent's reply is used only when code's checks pass; otherwise the template path runs.
No network: cloud.chat_json is stubbed."""
import pytest

from app import cloud, tg_agent
from app import telegram_bot as tb
from tests.test_entries_api import client, stub_models  # noqa: F401
from tests.test_telegram import SCRIPT, _f, _inbound, _out, linked  # noqa: F401


@pytest.fixture
def agent(linked, monkeypatch):  # noqa: F811
    calls = []
    state = {"reply": None, "error": None}

    def fake_chat_json(name, messages, schema, timeout):
        calls.append(messages)
        if state["error"]:
            raise cloud.CloudUnavailable(state["error"])
        text = messages[-1]["content"]
        return {**SCRIPT[text], "reply": state["reply"]}

    monkeypatch.setattr(tg_agent, "enabled", lambda: True)
    monkeypatch.setattr(cloud, "chat_json", fake_chat_json)
    return {"calls": calls, "state": state}


def test_agent_reply_is_sent_and_promise_reaches_inbox(agent):
    agent["state"]["reply"] = "धन्यवाद, नोट किया: आपने सोमवार को 5000 देने को कहा। मैं यह कैलाश जी की बात कामगार तक पहुँचा दूँगा।"
    res = _inbound("Somvaar ko 5000 dunga")
    last = _out()[-1]
    assert last["template_id"] == "AGENT" and last["text"] == agent["state"]["reply"]
    assert res["classification"]["agent"] == {"used": True, "rejected": None}
    assert res["classification"]["amount"] == 5000  # grounded by code from the message, as before
    facts = agent["calls"][0][1]["content"]
    assert facts.startswith("FACTS") and "days worked: 3" in facts
    items = client.get("/api/inbox", params={"worker_id": "w1"}).json()["items"]
    assert any(i["kind"] == "promise" for i in items)


@pytest.mark.parametrize("bad, reason", [
    ("ठीक है, आप 7000 दे दीजिए।", "UNGROUNDED_NUMBER"),  # number not in facts or chat
    ("नहीं दिया तो पुलिस में जाएँगे।", "BANNED_TERM"),
    ("ठीक है, 4000 में समझौता मंज़ूर है।", "BANNED_TERM"),
    ("", "EMPTY"),
])
def test_rejected_reply_falls_back_to_template(agent, bad, reason):
    agent["state"]["reply"] = bad
    res = _inbound("Somvaar ko 5000 dunga")
    last = _out()[-1]
    assert last["template_id"] != "AGENT" and last["text"] != bad
    assert res["classification"]["agent"] == {"used": False, "rejected": reason}


def test_hostile_never_reaches_the_agent(agent):
    agent["state"]["reply"] = "कोई बात नहीं"
    n = len(_out())
    res = _inbound("saale, phir paisa maanga to haath pair tod dunga")
    assert agent["calls"] == [] and len(_out()) == n and res["decision"].pause


def test_cloud_down_uses_local_classifier_and_templates(agent):
    agent["state"]["error"] = "CLOUD_HTTP"
    res = _inbound("abhi paisa nahi hai")
    assert res["classification"]["intent"] == "refuses"  # from the stubbed local classifier (SCRIPT)
    assert all(m["template_id"] != "AGENT" for m in _out())


def test_check_reply_words():
    assert tg_agent.check_reply("Noted, first thing tomorrow I will tell the worker.", "") is None  # "fir" ≠ "first"
    assert tg_agent.check_reply("We will file a complaint", "") == "BANNED_TERM"
    assert tg_agent.check_reply("₹१२,४०० बाकी (अनुमान)", "balance estimate: ₹12,400") is None
    assert tb.render("NEED_INVITE", "hi").startswith("नमस्ते")
