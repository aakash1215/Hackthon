"""ChatGPT agent for the Telegram chat with the thekedar (TG_AGENT=chatgpt; Akash's decision, 16 Oct).

It writes the reply on the worker's behalf, but code stays in charge:
- the deterministic hostile guard runs first (hostile = no reply, pause, alert) — this module is never called;
- the model gets only code-computed ledger facts (days, paid, balance *estimate*) and the recent chat;
- every reply is checked by code: no numbers that are not in the facts or the chat, no legal talk, no
  concessions / deals / promises for the worker, no threats; a failed check (or any API error) falls back
  to the fixed template reply in telegram_bot.classify_and_act;
- the same call also classifies the message (intent/amount/date/days) so promises still reach the inbox,
  grounded by api._ground_reply exactly like the local classifier.
"""
from __future__ import annotations

import copy
import re

from . import cloud
from .config import settings
from .contracts import json_schema_for
from .tg_policy import hostile_guard

MAX_CHARS = 500

# Words a reply for the worker must never contain (law, concessions/deals, "proof" wording). Lower-cased match.
BANNED = (
    # law / authorities (rule: never cites law)
    "धारा", "section", "court", "कोर्ट", "न्यायालय", "penalty", "जुर्माना", "पुलिस", "police", "केस", "fir",
    "शिकायत", "complaint", "कानून", "क़ानून", "law", "legal", "वकील", "lawyer", "labour office", "लेबर ऑफिस",
    "आयुक्त", "commissioner", "यूनियन", "union", "कायदा", "तक्रार", "पोलीस",
    # concessions / deals on the worker's behalf (rule: never negotiates or accepts a deal)
    "मंज़ूर", "मंजूर", "समझौता", "settle", "settlement", "deal", "accept", "माफ़", "माफ", "discount", "कम कर",
    "छोड़ देंगे", "छोड़ दो", "chalega", "चलेगा", "तडजोड",
    # wording rule 8
    "proof", "प्रूफ", "legally",
)

SYSTEM = """You are the 'Apna Hisaab' assistant. You write Telegram replies to a thekedar (labour contractor) \
on behalf of a construction worker, {worker}. The chat is recorded as the worker's record; the thekedar was told this.

Your job: be polite, calm and short (1-3 sentences). Reply in the language the thekedar writes in \
(Hindi, Marathi, English or Hinglish; default {lang_name}). Help the worker get clarity: how much is pending, \
when it will be paid, and a written hisaab. When the thekedar promises a payment, thank them and restate it \
exactly as they said it ("noted: you said ..."). When they ask or dispute, restate the worker's record using \
ONLY the FACTS below, and call the balance an estimate. If asked whether you are a person, say you are an \
automated assistant for {worker}. If something needs the worker's decision, say you will pass it to {worker}. \
Write naturally in one language; do not copy the English labels from FACTS ("paid so far", "balance estimate") \
into a Hindi or Marathi reply, and do not repeat the thekedar's whole message back.

Never: agree to less money, accept a deal or settlement, negotiate or bargain, waive anything, make any promise \
or commitment for the worker, give dates for the worker, threaten, mention law, police, court, union or complaints, \
argue or insult. Never invent a number or date: use only numbers in FACTS or in the thekedar's messages.

Also classify the thekedar's latest message: intent, confidence, and amount/date/days as {{value, evidence}} where \
evidence is an exact substring of that message (else null). Return JSON only."""

LANG_NAME = {"hi": "Hindi", "mr": "Marathi", "en": "English"}


def enabled() -> bool:
    return settings.tg_agent == "chatgpt" and settings.cloud_configured


def _schema() -> dict:
    s = copy.deepcopy(json_schema_for("thekedar_reply"))
    s["properties"]["reply"] = {"type": "string"}
    s["required"] = [*s["required"], "reply"]
    return s


def facts_text(vals: dict, thekedar: str, site: str) -> str:
    return (f"FACTS (from the worker's confirmed record, computed by code):\n"
            f"worker: {vals.get('worker')}\nthekedar: {thekedar}\nsite: {site}\nperiod: {vals.get('period')}\n"
            f"days worked: {vals.get('days')}\ndays (start–end):\n{vals.get('lines')}\n"
            f"paid so far: {vals.get('paid')}\nbalance estimate: {vals.get('balance') or 'not computed'}")


_DEV = str.maketrans("०१२३४५६७८९", "0123456789")


def _numbers(text: str) -> set[str]:
    t = (text or "").translate(_DEV)
    return {n.replace(",", "").lstrip("0") or "0" for n in re.findall(r"\d[\d,]*", t)}


def _banned(low: str) -> bool:
    # Latin terms match whole words only ("fir" must not hit "first"); Devanagari terms match as substrings.
    return any(re.search(r"\b" + re.escape(b) + r"\b", low) if b.isascii() else b in low for b in BANNED)


def check_reply(reply: str, *sources: str) -> str | None:
    """None if the reply may be sent, else the reason code (the caller falls back to a template)."""
    r = (reply or "").strip()
    if not r:
        return "EMPTY"
    if len(r) > MAX_CHARS:
        return "TOO_LONG"
    if _banned(r.lower()):
        return "BANNED_TERM"
    if hostile_guard(r):
        return "HOSTILE_TERM"
    allowed = set().union(*(_numbers(s) for s in sources))
    if _numbers(r) - allowed:
        return "UNGROUNDED_NUMBER"
    return None


def respond(vals: dict, thekedar: str, site: str, lang: str, history: list[dict], text: str) -> dict:
    """One ChatGPT call → {raw (classification incl. reply), reply (or None), rejected (reason or None)}.
    Raises cloud.CloudUnavailable on any API problem."""
    facts = facts_text(vals, thekedar, site)
    msgs = [{"role": "system", "content": SYSTEM.format(worker=vals.get("worker"), lang_name=LANG_NAME.get(lang, "Hindi"))},
            {"role": "system", "content": facts}]
    for h in history:
        msgs.append({"role": "user" if h["direction"] == "in" else "assistant", "content": h["text"]})
    msgs.append({"role": "user", "content": text})
    raw = cloud.chat_json("thekedar_agent", msgs, _schema(), 30)
    if "reply" not in raw and len(raw) == 1 and isinstance(next(iter(raw.values())), dict):
        raw = next(iter(raw.values()))  # schema is not strict: the model sometimes wraps the object once
    reply = (raw.get("reply") or "").strip()
    reason = check_reply(reply, facts, text, *(h["text"] for h in history))
    return {"raw": raw, "reply": None if reason else reply, "rejected": reason}


def history_rows(c, chat_id: int, exclude_id: str, n: int = 8) -> list[dict]:
    rows = c.execute("SELECT direction, text FROM tg_messages WHERE chat_id=? AND id != ? AND text IS NOT NULL "
                     "AND status IN ('pending','sent','received') ORDER BY created_at DESC, rowid DESC LIMIT ?",
                     (chat_id, exclude_id, n)).fetchall()
    return [{"direction": r["direction"], "text": r["text"]} for r in reversed(rows)]
