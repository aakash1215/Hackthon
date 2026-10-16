"""Telegram thekedar agent: fixed templates + reply policy (BUILD_PLAN §7). Pure and deterministic.

No message the bot sends is ever free LLM text: code picks a template id and fills it with values from
the ledger, the wage engine, or the thekedar's own grounded words. The LLM only classifies inbound
messages (thekedar_reply schema); a deterministic word guard can only escalate to `hostile`, never
downgrade. Never: negotiate, accept/reject an offer, mention penalties, sections or courts, threaten.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

LANGS = ("hi", "mr", "en")
DAILY_LIMIT = 5  # bot messages per chat per day

# {worker} etc. are filled by code. Balance is always labelled an estimate.
TEMPLATES: dict[str, dict[str, str]] = {
    "LANG_ASK": {
        "hi": "नमस्ते / नमस्कार / Hello — मैं {worker} का 'अपना हिसाब' सहायक हूँ। यह चैट रिकॉर्ड होती है। "
              "भाषा चुनें / भाषा निवडा / Choose a language:",
    },
    "INTRO": {
        "hi": "नमस्ते, मैं {worker} का 'अपना हिसाब' सहायक हूँ। इस चैट के संदेश {worker} के काम और भुगतान के "
              "रिकॉर्ड के रूप में सुरक्षित रखे जाते हैं।",
        "mr": "नमस्कार, मी {worker} यांचा 'आपला हिशोब' सहाय्यक आहे. या चॅटमधील संदेश {worker} यांच्या कामाच्या "
              "आणि पगाराच्या नोंदीसाठी जतन केले जातात.",
        "en": "Hello, I am the 'Apna Hisaab' assistant of {worker}. Messages in this chat are kept as a record "
              "of {worker}'s work and payments.",
    },
    "DAILY_UPDATE": {
        "hi": "आज {date}: {worker} ने {site} पर {start}–{end} काम किया। आज मिला: ₹{paid_today}। "
              "{worker} के रिकॉर्ड के अनुसार बाकी (अनुमान): ₹{balance}।",
        "mr": "आज {date}: {worker} यांनी {site} येथे {start}–{end} काम केले. आज मिळाले: ₹{paid_today}. "
              "{worker} यांच्या नोंदीनुसार बाकी (अंदाजे): ₹{balance}.",
        "en": "Today {date}: {worker} worked at {site} from {start} to {end}. Paid today: ₹{paid_today}. "
              "Balance by {worker}'s record (estimate): ₹{balance}.",
    },
    "DAY_UPDATE": {  # a confirmed day that is not today
        "hi": "{date}: {worker} ने {site} पर {start}–{end} काम किया। उस दिन मिला: ₹{paid_today}। "
              "{worker} के रिकॉर्ड के अनुसार बाकी (अनुमान): ₹{balance}।",
        "mr": "{date}: {worker} यांनी {site} येथे {start}–{end} काम केले. त्या दिवशी मिळाले: ₹{paid_today}. "
              "{worker} यांच्या नोंदीनुसार बाकी (अंदाजे): ₹{balance}.",
        "en": "{date}: {worker} worked at {site} from {start} to {end}. Paid that day: ₹{paid_today}. "
              "Balance by {worker}'s record (estimate): ₹{balance}.",
    },
    "PAYMENT_ACK": {
        "hi": "₹{amount} मिले, धन्यवाद। बाकी (अनुमान): ₹{balance}।",
        "mr": "₹{amount} मिळाले, धन्यवाद. बाकी (अंदाजे): ₹{balance}.",
        "en": "₹{amount} received, thank you. Balance (estimate): ₹{balance}.",
    },
    "SUMMARY": {
        "hi": "{worker} का हिसाब, {period}:\n{lines}\nकुल दिन: {days} · मिला: ₹{paid} · बाकी (अनुमान): ₹{balance}",
        "mr": "{worker} यांचा हिशोब, {period}:\n{lines}\nएकूण दिवस: {days} · मिळाले: ₹{paid} · बाकी (अंदाजे): ₹{balance}",
        "en": "{worker}'s record, {period}:\n{lines}\nDays: {days} · Paid: ₹{paid} · Balance (estimate): ₹{balance}",
    },
    "REQUEST_WRITTEN_HISAAB": {
        "hi": "कृपया लिखित हिसाब और बाकी रकम की तारीख बताएं। धन्यवाद।",
        "mr": "कृपया लेखी हिशोब आणि बाकी रकमेची तारीख कळवा. धन्यवाद.",
        "en": "Please share the written account and the date for the balance. Thank you.",
    },
    "NOTED_PROMISE": {
        "hi": "नोट कर लिया: ₹{amount}, {date}। धन्यवाद।",
        "mr": "नोंद केली: ₹{amount}, {date}. धन्यवाद.",
        "en": "Noted: ₹{amount}, {date}. Thank you.",
    },
    "NOTED_ASK_DATE": {
        "hi": "नोट कर लिया: ₹{amount}। कृपया तारीख बताएं। धन्यवाद।",
        "mr": "नोंद केली: ₹{amount}. कृपया तारीख कळवा. धन्यवाद.",
        "en": "Noted: ₹{amount}. Please tell the date. Thank you.",
    },
    "NOTED": {
        "hi": "नोट कर लिया। धन्यवाद।",
        "mr": "नोंद केली. धन्यवाद.",
        "en": "Noted. Thank you.",
    },
    "NOTED_WORKER_CONFIRMS": {
        "hi": "नोट कर लिया। {worker} इसकी पुष्टि करेंगे।",
        "mr": "नोंद केली. {worker} याची खात्री करतील.",
        "en": "Noted. {worker} will confirm this.",
    },
    "NOTED_DISPUTE": {
        "hi": "नोट कर लिया। {worker} के रिकॉर्ड में {days} दिन दर्ज हैं। कृपया अपना लिखित हिसाब भेजें।",
        "mr": "नोंद केली. {worker} यांच्या नोंदीत {days} दिवस आहेत. कृपया आपला लेखी हिशोब पाठवा.",
        "en": "Noted. {worker}'s record shows {days} days. Please send your written account.",
    },
}


def render(template_id: str, lang: str, **vals) -> str:
    t = TEMPLATES[template_id]
    text = t.get(lang) or t.get("hi")
    return text.format(**{k: ("—" if v is None else v) for k, v in vals.items()})


# --- deterministic hostile guard ------------------------------------------------------------
# Threats and abuse in hi / mr / Hinglish. Matching only escalates to hostile (no reply, pause, alert).
_HOSTILE_PHRASES = [
    "देख लूँगा", "देख लूंगा", "देख लेंगे", "मार दूँगा", "मार दूंगा", "मार डालूँगा", "मार डालूंगा", "मारूँगा", "मारूंगा",
    "तोड़ दूँगा", "तोड़ दूंगा", "तोड दूंगा", "हाथ-पैर", "हाथ पैर तोड़", "जान से", "निकाल दूँगा", "निकाल दूंगा",
    "बघून घेईन", "बघून घेतो", "मारीन", "मारून टाकीन", "तोडीन", "हाकलून देईन",
    "dekh lunga", "dekh loonga", "maar dunga", "mar dunga", "maar daalunga", "tod dunga", "haath pair",
    "jaan se", "nikal dunga", "nikaal dunga",
]
_ABUSE_WORDS = {
    "साला", "साले", "साली", "कुत्ता", "कुत्ते", "कुत्ती", "हरामी", "हरामखोर", "कमीना", "कमीने", "चूतिया", "चुतिया",
    "मादरचोद", "बहनचोद", "भेनचोद", "रांड", "भडवा", "भडव्या", "गांडू",
    "sala", "saala", "saale", "kutta", "kutte", "harami", "haramkhor", "kamina", "kamine", "chutiya",
    "madarchod", "behenchod", "bhenchod", "bc", "mc", "randi", "bhadwa", "gandu",
}
_WORD = re.compile(r"[\wऀ-ॿ]+")


def _norm(s: str) -> str:
    s = s.lower().replace("़", "")  # drop nukta so ड़ == ड
    return re.sub(r"\s+", " ", s)


_PHRASES_N = [_norm(p) for p in _HOSTILE_PHRASES]
_ABUSE_N = {_norm(w) for w in _ABUSE_WORDS}


def hostile_guard(text: str | None) -> str | None:
    """Return the matched phrase/word if the text is a threat or abuse, else None."""
    if not text:
        return None
    t = _norm(text)
    for p in _PHRASES_N:
        if p in t:
            return p
    for w in _WORD.findall(t):
        if w in _ABUSE_N:
            return w
    return None


# --- reply policy (BUILD_PLAN §7 table) --------------------------------------------------------

@dataclass(frozen=True)
class Decision:
    template_id: str | None  # None = no reply
    inbox_kind: str | None   # in-app item for the worker (None = nothing)
    pause: bool = False      # hostile: stop all automatic messages
    reason: str = ""


def decide(intent: str | None, confidence: str | None, *, amount=None, date_text=None,
           guard_hit: str | None = None) -> Decision:
    """Pick the reply template (or none) and the in-app item for one inbound thekedar message."""
    if guard_hit or intent == "hostile":
        return Decision(None, "hostile", pause=True, reason=f"hostile:{guard_hit or 'llm'}")
    if intent in (None, "other") or confidence != "high":
        return Decision(None, "message", reason="unclear")  # no reply; worker sees it verbatim
    if intent == "asks_details":
        return Decision("SUMMARY", None)
    if intent in ("acknowledges", "promise_to_pay"):
        if amount is not None and date_text:
            tpl = "NOTED_PROMISE"
        elif amount is not None:
            tpl = "NOTED_ASK_DATE"  # the date is asked when it is missing
        else:
            tpl = "NOTED"
        kind = "promise" if (intent == "promise_to_pay" or amount is not None) else "message"
        return Decision(tpl, kind)
    if intent == "partial_payment_claim":
        return Decision("NOTED_WORKER_CONFIRMS", "partial_payment")
    if intent in ("disputes_days", "disputes_rate"):
        return Decision("NOTED_DISPUTE", "dispute")
    if intent == "refuses":
        return Decision("NOTED", "refuses")
    return Decision(None, "message", reason="unhandled")
