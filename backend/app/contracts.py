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

TIME_FIELDS = {"start_time", "end_time"}
DATE_FIELDS = {"work_date", "payment_date"}
MONEY_FIELDS = {"amount_paid"}
INT_FIELDS = {"break_minutes"}
ENUM_FIELDS = {"worked": {"yes", "no", "unknown"}, "payment_mode": {"cash", "upi", "bank", "unknown"}}

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
    names = KIND_FIELDS[kind]
    return {
        "type": "object",
        "properties": {n: _FIELD for n in names},
        "required": names,
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
