"""Field lists, extraction JSON schemas and few-shot examples (Handoff §10.4, BUILD_PLAN §5).

Every extracted field is {value, evidence}. evidence must be an exact transcript substring
(checked by reconcile.py), otherwise the value is dropped.
"""
from __future__ import annotations

KIND_FIELDS: dict[str, list[str]] = {
    "workday": [
        "work_date", "start_time", "end_time", "break_minutes", "worked", "site",
        "contractor_name", "contractor_phone", "principal_employer", "work_type",
        "agreed_rate", "coworkers_present", "incidents", "notes",
    ],
    "payment": [
        "payment_date", "amount_paid", "payment_mode", "payer_name",
        "covers_from", "covers_to", "deductions",
    ],
    "hisaab_statement": [
        "days_counted", "rate_per_day", "gross_amount", "deductions",
        "paid_now", "balance_promised", "promised_date",
    ],
    "coworker_confirm": ["coworker_name", "dates_or_days", "site", "consent_phrase"],
}
# Kinds stored as entries. Extra extraction-only schemas (thekedar_reply) live in SCHEMA_FIELDS.
ENTRY_KINDS = tuple(KIND_FIELDS)

# thekedar_reply (BUILD_PLAN §5): run on thekedar recordings (and, in P4, Telegram messages).
REPLY_INTENTS = (
    "acknowledges", "promise_to_pay", "partial_payment_claim", "disputes_days", "disputes_rate",
    "asks_details", "refuses", "hostile", "other",
)
SCHEMA_FIELDS: dict[str, list[str]] = {
    **KIND_FIELDS,
    "thekedar_reply": ["intent", "confidence", "amount", "date", "days"],
}

TIME_FIELDS = {"start_time", "end_time"}
DATE_FIELDS = {"work_date", "payment_date"}
MONEY_FIELDS = {"amount_paid"}
INT_FIELDS = {"break_minutes"}
# hisaab_statement numbers: the LLM value is checked against a code parse of its own evidence span
# (P0: the CPU LLM misreads number words, e.g. पाँच सौ → 5000).
SPAN_MONEY_FIELDS = {"rate_per_day", "gross_amount", "deductions", "paid_now", "balance_promised"}
SPAN_INT_FIELDS = {"days_counted"}
ENUM_FIELDS = {
    "worked": {"yes", "no", "unknown"},
    "payment_mode": {"cash", "upi", "bank", "unknown"},
    "intent": set(REPLY_INTENTS),
}

_FIELD = {
    "type": "object",
    "properties": {
        "value": {"type": ["string", "number", "null"]},
        "evidence": {"type": ["string", "null"]},
    },
    "required": ["value", "evidence"],
    "additionalProperties": False,
}


def json_schema_for(kind: str) -> dict:
    if kind == "thekedar_reply":
        return _REPLY_SCHEMA
    names = KIND_FIELDS[kind]
    return {
        "type": "object",
        "properties": {n: _FIELD for n in names},
        "required": names,
        "additionalProperties": False,
    }


_REPLY_SCHEMA = {
    "type": "object",
    "properties": {
        "intent": {"type": "string", "enum": list(REPLY_INTENTS)},
        "confidence": {"type": "string", "enum": ["high", "low"]},
        "amount": _FIELD,
        "date": _FIELD,
        "days": _FIELD,
    },
    "required": ["intent", "confidence", "amount", "date", "days"],
    "additionalProperties": False,
}


def _null_fill(kind: str, partial: dict) -> dict:
    out = {n: {"value": None, "evidence": None} for n in KIND_FIELDS[kind]}
    out.update(partial)
    return out


def _f(value, evidence):
    return {"value": value, "evidence": evidence}


# (transcript, expected JSON). Evidence strings are copied exactly from the transcript.
FEW_SHOT: dict[str, list[tuple[str, dict]]] = {
    "workday": [
        (
            "आज सुबह नौ बजे से शाम सात बजे तक काम किया।",
            _null_fill("workday", {
                "work_date": _f("आज", "आज"),
                "start_time": _f("9:00 AM", "सुबह नौ बजे"),
                "end_time": _f("7:00 PM", "शाम सात बजे"),
                "worked": _f("yes", "काम किया"),
            }),
        ),
        (
            "काल सकाळी नऊ वाजता कामावर गेलो आणि संध्याकाळी सहा वाजता सुटलो.",
            _null_fill("workday", {
                "work_date": _f("काल", "काल"),
                "start_time": _f("9:00 AM", "सकाळी नऊ वाजता"),
                "end_time": _f("6:00 PM", "संध्याकाळी सहा वाजता"),
                "worked": _f("yes", "कामावर गेलो"),
            }),
        ),
    ],
    "payment": [
        (
            "ठेकेदार ने आज दो हजार रुपये cash में diye।",
            _null_fill("payment", {
                "payment_date": _f("आज", "आज"),
                "amount_paid": _f("2000", "दो हजार रुपये"),
                "payment_mode": _f("cash", "cash में"),
                "payer_name": _f("ठेकेदार", "ठेकेदार"),
            }),
        ),
    ],
}

FEW_SHOT["hisaab_statement"] = [
    (
        "ठेकेदार बोला 12 दिन, 600 रोज़, 2000 उचल काटी, बाकी सोमवार को देगा।",
        _null_fill("hisaab_statement", {
            "days_counted": _f(12, "12 दिन"),
            "rate_per_day": _f(600, "600 रोज़"),
            "deductions": _f(2000, "2000 उचल काटी"),
            "promised_date": _f("सोमवार", "सोमवार"),
        }),
    ),
    (
        "बारा दिवसाचे सहाशे रुपये रोज, आज तीन हजार दिले.",
        _null_fill("hisaab_statement", {
            "days_counted": _f(12, "बारा दिवसाचे"),
            "rate_per_day": _f(600, "सहाशे रुपये रोज"),
            "paid_now": _f(3000, "तीन हजार दिले"),
        }),
    ),
]
FEW_SHOT["coworker_confirm"] = [
    (
        "मेरा नाम रमेश है, रिकॉर्ड करने के लिए राज़ी हूँ। सुनीता एक से तेरह तारीख तक मेरे साथ साइट पर थी।",
        _null_fill("coworker_confirm", {
            "coworker_name": _f("रमेश", "मेरा नाम रमेश है"),
            "dates_or_days": _f("एक से तेरह तारीख तक", "एक से तेरह तारीख तक"),
            "site": _f("साइट", "साइट पर"),
            "consent_phrase": _f("राज़ी हूँ", "रिकॉर्ड करने के लिए राज़ी हूँ"),
        }),
    ),
]
REPLY_FEW_SHOT = [
    ("Somvaar ko 5000 dunga", {"intent": "promise_to_pay", "confidence": "high",
                                "amount": _f(5000, "5000"), "date": _f("Somvaar", "Somvaar"), "days": _f(None, None)}),
    ("अभी पैसा नहीं है", {"intent": "refuses", "confidence": "high",
                          "amount": _f(None, None), "date": _f(None, None), "days": _f(None, None)}),
    ("12 दिन ही काम किया, 13 नहीं", {"intent": "disputes_days", "confidence": "high",
                                      "amount": _f(None, None), "date": _f(None, None), "days": _f(12, "12 दिन")}),
    ("हो, तुझे पूरे दिन लिखे हैं, हिसाब ठीक है", {"intent": "acknowledges", "confidence": "high",
                                                  "amount": _f(None, None), "date": _f(None, None), "days": _f(None, None)}),
    ("फिर पैसा माँगा तो हाथ-पैर तोड़ दूँगा", {"intent": "hostile", "confidence": "high",
                                            "amount": _f(None, None), "date": _f(None, None), "days": _f(None, None)}),
]

REPLY_SYSTEM_PROMPT = (
    "You classify what a construction contractor (thekedar) said about a worker's wages. "
    "Pick one intent: acknowledges (agrees the work/amount is owed), promise_to_pay, partial_payment_claim "
    "(says he already paid some), disputes_days, disputes_rate, asks_details, refuses, hostile (abuse or threats), other. "
    "confidence is low if unsure. amount, date and days must quote the transcript exactly in evidence, else null. "
    "Do not compute anything. Output only JSON that matches the schema."
)

SYSTEM_PROMPT = (
    "You copy facts from a construction worker's voice-note transcript (Hindi, Marathi or Hinglish). "
    "Every value must quote the transcript in `evidence`, copied exactly from it. "
    "If a fact is not said, use null for both value and evidence. "
    "Do not compute totals, durations or unit conversions. "
    "Do not resolve relative dates; return the words as spoken (for example 'कल'). "
    "The recording date and the worker's defaults are context, not facts: "
    "do not copy them into a value unless the transcript says it. "
    "Output only JSON that matches the schema."
)
