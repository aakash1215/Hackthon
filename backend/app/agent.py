"""सहायक (helper agent): answers the worker's questions about their own record and helps them reach the thekedar.

Same rules as the rest of the product:
- the LLM only *classifies* the question into a fixed intent (closed JSON schema). A keyword matcher runs
  first, so the common questions work without any model;
- every answer is a fixed Hindi template filled by code from the worker's own confirmed data (wage engine,
  ledger, Telegram tables). No LLM text, no arithmetic by the model, no legal advice;
- the agent never messages the thekedar by itself. It *offers* one of the fixed Telegram templates and the
  worker taps to send it (POST /api/telegram/send, rate-limited and logged by the Telegram module).
"""
from __future__ import annotations

import json
import logging
import re
from datetime import date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from . import api, db, extract
from .config import settings

log = logging.getLogger("apna_hisaab.agent")
router = APIRouter()

INTENTS = (
    "money_due", "days_worked", "paid_total", "min_wage", "thekedar_status", "send_summary",
    "ask_written_hisaab", "connect_thekedar", "how_record_day", "how_record_payment", "record_thekedar",
    "make_file", "danger", "help", "other",
)
PERIODS = ("today", "this_week", "last_week", "this_month", "last_month", "all")

SUGGESTIONS = [
    "मेरा कितना पैसा बाकी है?",
    "इस हफ़्ते कितने दिन काम किया?",
    "अब तक कितने पैसे मिले?",
    "मेरी सरकारी मज़दूरी कितनी है?",
    "ठेकेदार ने क्या जवाब दिया?",
    "ठेकेदार को हिसाब भेजो",
]


# --- 1. understand the question: keywords first, then (only if unclear) the LLM as a classifier ----------

def _norm(s: str) -> str:
    s = (s or "").lower().replace("़", "").replace("ँ", "ं")  # nukta and chandrabindu spellings vary
    return re.sub(r"\s+", " ", s).strip()


def _has(t: str, *words: str) -> bool:
    return any(_norm(w) in t for w in words)


def _words(t: str) -> set[str]:
    return set(re.findall(r"[\wऀ-ॿ]+", t))  # whole words, for short ones like मारा (not inside हमारा)


_THEKEDAR = ("ठेकेदार", "ठेकेदर", "थेकेदार", "मुकादम", "कॉन्ट्रैक्टर", "thekedar", "contractor", "seth", "सेठ", "मालिक")
_SEND = ("भेज", "भेजो", "भेजना", "send", "पाठव", "बता दो", "बताओ उसे")
_HOW = ("कैसे", "कैसा", "how", "कसे", "कसं", "क्या करूं", "क्या करना")


def keyword_intent(text: str) -> str:
    t = _norm(text)
    if not t:
        return "other"
    if _has(t, "धमकी", "धमका", "मारने", "मारूंगा", "मारेगा", "पीटा", "पिटाई", "गाली", "डरा रहा", "मारहाण", "threat") \
            or _words(t) & {"मारा", "मार", "पीट", "beat"}:
        return "danger"
    if _has(t, "लिखित", "लिखकर", "लिख कर", "written") or (_has(t, "मांग", "मागा", "माग") and _has(t, "हिसाब")):
        return "ask_written_hisaab"
    if _has(t, *_SEND) and (_has(t, *_THEKEDAR) or _has(t, "हिसाब", "सार", "summary", "रिपोर्ट")):
        return "send_summary"
    if _has(t, "telegram", "टेलीग्राम", "टेलिग्राम") and _has(t, "जोड़", "जोड", "जुड़", "जुड", "connect", "link"):
        return "connect_thekedar"
    if _has(t, *_THEKEDAR) and _has(t, "जवाब", "बोला", "कहा", "reply", "वादा", "promise", "मैसेज", "message",
                                     "संदेश", "telegram", "टेलीग्राम", "उत्तर", "म्हणाला"):
        return "thekedar_status"
    if _has(t, *_HOW) and _has(t, "पैसा", "पैसे", "पेमेंट", "payment", "रुपये", "मिले पैसे"):
        return "how_record_payment"
    if _has(t, "रिकॉर्ड", "रिकार्ड", "record") and _has(t, *_THEKEDAR):
        return "record_thekedar"
    if _has(t, *_HOW) and _has(t, "रिकॉर्ड", "रिकार्ड", "record", "दर्ज", "हाजिरी", "हजेरी", "दिन", "काम"):
        return "how_record_day"
    if _has(t, "फाइल", "file", "pdf", "केस", "शिकायत", "complaint", "लेबर ऑफिस", "labour office", "तक्रार"):
        return "make_file"
    if _has(t, "न्यूनतम", "minimum", "सरकारी दर", "सरकारी मजदूरी", "सरकारी रेट", "रेट", "rate", "किमान", "दर कितनी",
            "मजदूरी कितनी", "रोज़ कितना", "रोज कितना"):
        return "min_wage"
    if _has(t, "बाकी", "बकाया", "due", "बनता", "उधार", "थकबाकी", "लेना है", "बाकि", "owed"):
        return "money_due"
    if _has(t, "मिला", "मिले", "मिली", "दिया", "दिए", "दिये", "paid", "मिळाले", "दिले", "payment", "पेमेंट"):
        return "paid_total"
    if _has(t, "दिन", "days", "दिवस", "हाजिरी", "हजेरी") and _has(t, "कितने", "कितना", "किती", "how many", "काम"):
        return "days_worked"
    if _has(t, "मदद", "help", "क्या कर सकत", "क्या पूछ", "मदत"):
        return "help"
    return "other"


def keyword_period(text: str) -> str:
    t = _norm(text)
    if _has(t, "पिछले हफ्ते", "पिछला हफ्ता", "पिछले सप्ताह", "last week", "मागच्या आठवड"):
        return "last_week"
    if _has(t, "पिछले महीने", "पिछला महीना", "last month", "मागच्या महिन"):
        return "last_month"
    if _has(t, "इस हफ्ते", "इस सप्ताह", "this week", "हफ्ते", "सप्ताह", "आठवड", "week"):
        return "this_week"
    if _has(t, "इस महीने", "this month", "महीने", "महिन", "month"):
        return "this_month"
    if _has(t, "आज", "today", "आज का"):
        return "today"
    return "all"


_SCHEMA = {
    "type": "object",
    "properties": {"intent": {"type": "string", "enum": list(INTENTS)},
                   "period": {"type": "string", "enum": list(PERIODS)}},
    "required": ["intent", "period"],
    "additionalProperties": False,
}
_SYSTEM = (
    "You sort a construction worker's question (Hindi, Marathi or Hinglish) into ONE intent from the list. "
    "Do not answer the question. Output JSON only.\n"
    "money_due: how much money is still owed. days_worked: how many days worked. paid_total: how much was paid. "
    "min_wage: the government minimum wage rate. thekedar_status: what the contractor replied or promised. "
    "send_summary: send my work summary to the contractor. ask_written_hisaab: ask the contractor for a written account. "
    "connect_thekedar: connect the contractor on Telegram. how_record_day / how_record_payment: how to use the app "
    "to record a work day / a payment. record_thekedar: record what the contractor says. make_file: make the evidence "
    "file / complaint. danger: the worker is threatened, beaten or scared. help: what can you do. other: anything else.\n"
    "period: the time the question is about, or 'all'."
)
_FEW = [
    ("सेठ ने पैसे कब देने को बोला था", {"intent": "thekedar_status", "period": "all"}),
    ("पिछले हफ्ते का पूरा पैसा मिल गया क्या", {"intent": "paid_total", "period": "last_week"}),
    ("मुझे कोर्ट जाना है कागज़ चाहिए", {"intent": "make_file", "period": "all"}),
]


def classify(text: str, engine: str | None = None) -> tuple[str, str, str]:
    """→ (intent, period, source). source: keywords | llm | none."""
    intent, period = keyword_intent(text), keyword_period(text)
    if intent != "other" or len(_norm(text)) < 4:
        return intent, period, "keywords"
    msgs: list[dict] = [{"role": "system", "content": _SYSTEM}]
    for q, out in _FEW:
        msgs += [{"role": "user", "content": q}, {"role": "assistant", "content": json.dumps(out, ensure_ascii=False)}]
    msgs.append({"role": "user", "content": text[:300]})
    try:
        out = extract.classify("worker_question", msgs, _SCHEMA, timeout=45,
                               **({"engine": "cloud"} if engine == "cloud" else {}))
    except extract.LLMUnavailable as e:
        log.info("agent classifier unavailable (%s)", e)
        return "other", period, "none"
    li = out.get("intent") if out.get("intent") in INTENTS else "other"
    lp = out.get("period") if out.get("period") in PERIODS else "all"
    return li, (period if period != "all" else lp), "llm"


# --- 2. answer: fixed templates filled by code ------------------------------------------------------------

_MONTHS = ["जनवरी", "फ़रवरी", "मार्च", "अप्रैल", "मई", "जून", "जुलाई", "अगस्त", "सितंबर", "अक्टूबर", "नवंबर", "दिसंबर"]
_PERIOD_HI = {"today": "आज", "this_week": "इस हफ़्ते", "last_week": "पिछले हफ़्ते", "this_month": "इस महीने",
              "last_month": "पिछले महीने", "all": "अब तक"}
_CATEGORY_HI = {"unskilled": "अकुशल (हेल्पर)", "semi_skilled": "अर्ध-कुशल", "skilled": "कुशल (मिस्त्री)",
                "highly_skilled": "अति-कुशल"}
_ERR_HI = {
    "SITE_NOT_SET": "काम की जगह नहीं भरी गई है",
    "NO_CONFIRMED_DAYS": "अभी कोई पक्का किया हुआ दिन नहीं है",
    "CATEGORY_UNKNOWN": "आपके काम का प्रकार पक्का नहीं है",
    "ZONE_UNCONFIRMED": "काम की जगह का ज़ोन पक्का नहीं है",
    "SPHERE_UNKNOWN": "यह पक्का नहीं कि सरकारी (राज्य/केंद्र) कौन-सी दर लगेगी",
}
_REPLY_HI = {
    "acknowledges": "हिसाब देखा / माना", "promise_to_pay": "पैसे देने का वादा किया",
    "partial_payment_claim": "कहा कि कुछ पैसे दे दिए", "disputes_days": "दिनों की गिनती पर असहमति जताई",
    "disputes_rate": "रेट पर असहमति जताई", "asks_details": "और जानकारी माँगी", "refuses": "मना किया",
    "hostile": "गलत / धमकी भरी बात लिखी", "other": "एक संदेश भेजा",
}


def _rupees(v) -> str:
    n = int(Decimal(str(v or 0)).quantize(Decimal(1), rounding=ROUND_HALF_UP))
    s = str(abs(n))
    if len(s) > 3:  # Indian grouping: 1,23,456
        head, tail = s[:-3], s[-3:]
        head = re.sub(r"(\d)(?=(\d\d)+$)", r"\1,", head)
        s = f"{head},{tail}"
    return f"₹{'-' if n < 0 else ''}{s}"


def _day_hi(iso: str | None) -> str:
    try:
        d = date.fromisoformat((iso or "")[:10])
    except ValueError:
        return ""
    return f"{d.day} {_MONTHS[d.month - 1]}"


def period_range(period: str, today: date) -> tuple[date | None, date | None]:
    if period == "today":
        return today, today
    if period == "this_week":
        start = today - timedelta(days=today.weekday())
        return start, today
    if period == "last_week":
        start = today - timedelta(days=today.weekday() + 7)
        return start, start + timedelta(days=6)
    if period == "this_month":
        return today.replace(day=1), today
    if period == "last_month":
        end = today.replace(day=1) - timedelta(days=1)
        return end.replace(day=1), end
    return None, None


def _in(d: str | None, lo: date | None, hi: date | None) -> bool:
    if lo is None:
        return True
    try:
        x = date.fromisoformat((d or "")[:10])
    except ValueError:
        return False
    return lo <= x <= hi


def _go(screen: str, label: str, params: dict | None = None) -> dict:
    return {"type": "go", "screen": screen, "label": label, "params": params or {}}


def _pending_count(c, worker_id: str) -> int:
    return c.execute("SELECT COUNT(*) FROM entries WHERE worker_id=? AND status IN ('saved','processed') "
                     "AND kind IN ('workday','payment') AND (error IS NULL OR error != 'CONSENT_REFUSED')",
                     (worker_id,)).fetchone()[0]


def _tg_state(c, worker_id: str) -> dict:
    link = c.execute("SELECT * FROM tg_links WHERE worker_id=? AND linked_at IS NOT NULL ORDER BY linked_at DESC "
                     "LIMIT 1", (worker_id,)).fetchone()
    return {"configured": settings.telegram_configured, "link": dict(link) if link else None}


def _a_money_due(worker_id: str, period: str, today: date) -> dict:
    lo, hi = period_range(period, today)
    h = api.hisaab(worker_id, lo.isoformat() if lo else None, hi.isoformat() if hi else None)
    if not h.get("ok") or not h.get("totals"):
        why = "; ".join(_ERR_HI.get(e if isinstance(e, str) else e.get("code"), "कुछ जानकारी अधूरी है")
                        for e in (h.get("errors") or [])) or "कुछ जानकारी अधूरी है"
        return {"text": f"अभी रक़म नहीं बता सकती: {why}। पहले अपने दिन और पैसे पक्के करें।",
                "actions": [_go("ledger", "खाता देखें")]}
    t = h["totals"]
    n = len([d for d in h.get("days", []) if not d.get("error")])
    text = (f"{_PERIOD_HI[period]} आपके पक्के किए {n} दिनों का सरकारी न्यूनतम दर से {_rupees(t['due_statutory'])} "
            f"बनता है। आपको {_rupees(t['paid_total'])} मिले। लगभग {_rupees(t['claim_estimate'])} बाकी हो सकते हैं। "
            f"यह अनुमान है।")
    return {"text": text, "actions": [_go("hisaab", "पूरा हिसाब देखें")]}


def _a_days(worker_id: str, period: str, today: date) -> dict:
    lo, hi = period_range(period, today)
    lg = api.ledger(worker_id)
    days = [d for d in lg["days"] if _in(d["date"], lo, hi) and d.get("worked") != "no"]
    with db.read() as c:
        pending = _pending_count(c, worker_id)
    text = f"{_PERIOD_HI[period]} आपने {len(days)} दिन काम किया (पक्के किए हुए)।"
    if days:
        text += f" आख़िरी दिन: {_day_hi(max(d['date'] for d in days))}।"
    if pending:
        text += f" {pending} रिकॉर्डिंग अभी पक्की करनी बाकी है।"
    return {"text": text, "actions": [_go("ledger", "खाता देखें")]}


def _a_paid(worker_id: str, period: str, today: date) -> dict:
    lo, hi = period_range(period, today)
    lg = api.ledger(worker_id)
    pays = [p for p in lg["payments"] if _in(p["date"], lo, hi) and p.get("amount") is not None]
    if not pays:
        return {"text": f"{_PERIOD_HI[period]} कोई पक्का किया हुआ पैसा नहीं मिला। पैसा मिले तो उसी दिन बोलकर सेव करें।",
                "actions": [_go("record", "पैसा मिला — बोलें", {"kind": "payment"})]}
    total = sum(Decimal(str(p["amount"])) for p in pays)
    last = max(pays, key=lambda p: p["date"] or "")
    text = (f"{_PERIOD_HI[period]} आपको {len(pays)} बार में कुल {_rupees(total)} मिले। "
            f"आख़िरी बार {_day_hi(last['date'])} को {_rupees(last['amount'])}।")
    return {"text": text, "actions": [_go("ledger", "खाता देखें")]}


def _a_min_wage(worker_id: str, today: date) -> dict:
    h = api.hisaab(worker_id)
    with db.read() as c:
        w = api._row(c, "workers", worker_id) or {}
    rows = [d for d in h.get("days", []) if d.get("daily_min")]
    if not rows:
        why = "; ".join(_ERR_HI.get(e if isinstance(e, str) else e.get("code"), "कुछ जानकारी अधूरी है")
                        for e in (h.get("errors") or [])) or "कोई पक्का दिन नहीं है"
        return {"text": f"अभी दर नहीं बता सकती: {why}।", "actions": [_go("settings", "सेटिंग्स देखें")]}
    r = rows[-1]
    cat = _CATEGORY_HI.get(w.get("category"), "आपके काम")
    text = (f"{cat} के लिए आपकी जगह पर सरकारी न्यूनतम मज़दूरी लगभग {_rupees(r['daily_min'])} प्रति दिन है "
            f"(दर-सूची {r.get('pack_id')})। ज़्यादा घंटों का पैसा अलग से जुड़ता है। यह अनुमान है।")
    return {"text": text, "actions": [_go("hisaab", "हिसाब देखें")]}


def _a_thekedar(worker_id: str) -> dict:
    with db.read() as c:
        tg = _tg_state(c, worker_id)
        last_in = c.execute("SELECT tg_date, classification FROM tg_messages WHERE worker_id=? AND direction='in' "
                            "ORDER BY created_at DESC, rowid DESC LIMIT 1", (worker_id,)).fetchone()
        proms = [dict(r) for r in c.execute("SELECT amount, due_date FROM promises WHERE worker_id=? AND confirmed=1 "
                                            "ORDER BY created_at DESC LIMIT 3", (worker_id,))]
        new_inbox = c.execute("SELECT COUNT(*) FROM inbox WHERE worker_id=? AND status='new'", (worker_id,)).fetchone()[0]
    if not tg["configured"]:
        return {"text": "इस हब पर Telegram अभी चालू नहीं है। ठेकेदार की बात रिकॉर्ड करनी हो तो नीचे दबाएँ।",
                "actions": [_go("recordOther", "ठेकेदार की बात रिकॉर्ड करें", {"who": "thekedar"})]}
    if not tg["link"]:
        return {"text": "ठेकेदार अभी Telegram पर आपसे नहीं जुड़े हैं। जुड़ने के बाद उनके हर जवाब का रिकॉर्ड यहाँ दिखेगा।",
                "actions": [_go("telegram", "ठेकेदार को जोड़ें")]}
    parts = []
    if last_in:
        cl = json.loads(last_in["classification"]) if last_in["classification"] else {}
        parts.append(f"ठेकेदार का आख़िरी जवाब {_day_hi(last_in['tg_date'])} को आया: उन्होंने "
                     f"{_REPLY_HI.get(cl.get('intent'), _REPLY_HI['other'])}।")
    else:
        parts.append("ठेकेदार Telegram पर जुड़े हैं, पर अभी तक कोई जवाब नहीं आया।")
    for p in proms:
        parts.append(f"पक्का किया वादा: {_rupees(p['amount'])}" + (f", {_day_hi(p['due_date'])} तक" if p["due_date"] else "") + "।")
    if new_inbox:
        parts.append(f"{new_inbox} नए जवाब आपको देखने हैं।")
    if tg["link"].get("paused"):
        parts.append("बातचीत अभी रुकी हुई है।")
    return {"text": " ".join(parts), "actions": [_go("telegram", "बातचीत देखें")]}


_TEMPLATE_HI = {
    "SUMMARY": ("आपके पक्के किए दिनों और मिले पैसों का तय सार", "हाँ, सार भेजें"),
    "REQUEST_WRITTEN_HISAAB": ("लिखित हिसाब माँगने का तय संदेश", "हाँ, लिखित हिसाब माँगें"),
}


def _a_send(worker_id: str, template: str) -> dict:
    with db.read() as c:
        tg = _tg_state(c, worker_id)
    if not tg["configured"]:
        return {"text": "इस हब पर Telegram अभी चालू नहीं है, इसलिए संदेश नहीं भेज सकती।", "actions": []}
    if not tg["link"]:
        return {"text": "पहले ठेकेदार को Telegram पर जोड़ना होगा। फिर मैं तय संदेश भेज सकती हूँ।",
                "actions": [_go("telegram", "ठेकेदार को जोड़ें")]}
    if tg["link"].get("paused"):
        return {"text": "ठेकेदार से बातचीत अभी रुकी हुई है। पहले बातचीत चालू करें।",
                "actions": [_go("telegram", "बातचीत देखें")]}
    what, label = _TEMPLATE_HI[template]
    return {"text": f"मैं ठेकेदार को Telegram पर {what} भेज सकती हूँ। संदेश पहले से तय है — मैं अपनी तरफ़ से कुछ "
                    f"नहीं लिखती, न कोई सौदा करती हूँ। भेजूँ?",
            "actions": [{"type": "tg_send", "template": template, "label": label}, _go("telegram", "पहले बातचीत देखें")]}


_STATIC = {
    "connect_thekedar": ("ठेकेदार को Telegram पर जोड़ने के लिए उन्हें एक लिंक या QR भेजें। जुड़ने पर बॉट बताता है कि "
                         "बातचीत रिकॉर्ड होती है।", [_go("telegram", "ठेकेदार को जोड़ें")]),
    "how_record_day": ("‘आज’ पर बड़ा माइक दबाएँ और बोलें: कब काम शुरू किया, कब ख़त्म, बीच में कितनी छुट्टी। "
                       "फिर स्क्रीन पर देखकर पक्का करें।", [_go("record", "अभी बोलें", {"kind": "workday"})]),
    "how_record_payment": ("जिस दिन पैसा मिले, ‘पैसा मिला’ दबाकर बोलें: कितने रुपये, किसने दिए, नकद या ऑनलाइन। "
                           "रसीद या स्क्रीनशॉट की फ़ोटो भी जोड़ सकते हैं।",
                           [_go("record", "पैसा मिला — बोलें", {"kind": "payment"})]),
    "record_thekedar": ("ठेकेदार की बात रिकॉर्ड करने से पहले ऐप उन्हें सुनाता है कि रिकॉर्डिंग हो रही है और उनकी "
                        "मंज़ूरी लेता है। छुपकर रिकॉर्ड नहीं होता।",
                        [_go("recordOther", "ठेकेदार की बात रिकॉर्ड करें", {"who": "thekedar"})]),
    "make_file": ("‘फ़ाइल’ टैब में आपकी सबूत फ़ाइल (PDF) बनती है: दिन, पैसे, हिसाब का अनुमान और हर रिकॉर्डिंग का "
                  "हैश। इसे यूनियन या सहायक को दिखा सकते हैं।", [_go("file", "फ़ाइल बनाएँ")]),
    "danger": ("आपकी सुरक्षा सबसे पहले है। अभी ठेकेदार से बहस न करें। यूनियन / सहायक को फ़ोन करें। आपका रिकॉर्ड हब पर "
               "सुरक्षित है।", [{"type": "call_union", "label": "यूनियन / सहायक को कॉल करें"}]),
    "help": ("मैं आपके अपने रिकॉर्ड से बता सकती हूँ: कितने दिन काम किया, कितने पैसे मिले, कितना बाकी हो सकता है, "
             "सरकारी दर, और ठेकेदार ने क्या जवाब दिया। मैं ठेकेदार को तय संदेश भी भेज सकती हूँ — आपके कहने पर ही।", []),
    "other": ("माफ़ कीजिए, यह मैं नहीं समझ पाई। मैं सिर्फ़ आपके रिकॉर्ड और ठेकेदार से जुड़े सवालों में मदद करती हूँ। "
              "नीचे से कोई सवाल चुनें।", []),
}


def answer(worker_id: str, intent: str, period: str, today: date | None = None) -> dict:
    today = today or date.today()
    if intent == "money_due":
        return _a_money_due(worker_id, period, today)
    if intent == "days_worked":
        return _a_days(worker_id, period, today)
    if intent == "paid_total":
        return _a_paid(worker_id, period, today)
    if intent == "min_wage":
        return _a_min_wage(worker_id, today)
    if intent == "thekedar_status":
        return _a_thekedar(worker_id)
    if intent == "send_summary":
        return _a_send(worker_id, "SUMMARY")
    if intent == "ask_written_hisaab":
        return _a_send(worker_id, "REQUEST_WRITTEN_HISAAB")
    text, actions = _STATIC.get(intent, _STATIC["other"])
    return {"text": text, "actions": list(actions)}


class AskIn(BaseModel):
    worker_id: str
    text: str = ""
    intent: Literal[INTENTS] | None = None  # a tapped suggestion chip can skip classification  # type: ignore[valid-type]
    period: Literal[PERIODS] | None = None  # type: ignore[valid-type]
    engine: str = "local"


@router.post("/api/agent/ask")
def ask(body: AskIn):
    with db.read() as c:
        if not api._row(c, "workers", body.worker_id):
            raise HTTPException(404, "WORKER_NOT_FOUND")
    text = (body.text or "").strip()[:500]
    if body.intent:
        intent, period, source = body.intent, body.period or keyword_period(text), "chip"
    else:
        if not text:
            raise HTTPException(422, "EMPTY_QUESTION")
        intent, period, source = classify(text, body.engine)
    out = answer(body.worker_id, intent, period)
    return {"intent": intent, "period": period, "source": source, **out,
            "suggestions": SUGGESTIONS if intent in ("other", "help") else [],
            "ts": datetime.now().isoformat(timespec="seconds")}


@router.get("/api/agent/suggestions")
def suggestions():
    return {"items": SUGGESTIONS}
