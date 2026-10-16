"""Reconciler (Handoff §10.6): two readers (LLM + normalizer), grounding, ASR confidence, plausibility.

Colours: green = both readers agree on a stated value · amber = prefill or disagreement, the worker
must confirm · red = nobody found it, the worker must fill it · none = optional text not said.
"""
from __future__ import annotations

import re
from datetime import date

from .contracts import DATE_FIELDS, INT_FIELDS, KIND_FIELDS, MONEY_FIELDS, TIME_FIELDS
from .normalize import key, parse_clock, parse_date, parse_money

LOW_LOGPROB = -1.0
HIGH_NO_SPEECH = 0.5
AMOUNT_FLAG = 5000
MAX_HOURS = 16
LATE_DAYS = 7


def _squash(s: str) -> str:
    """Whitespace removed, digits and nukta normalised: the comparison used for grounding."""
    return re.sub(r"\s+", "", key(s))


def _grounded(evidence: str | None, transcript: str) -> bool:
    if not evidence or not _squash(evidence):
        return False
    return _squash(evidence) in _squash(transcript)


def _asr_low(evidence: str, segments: list[dict] | None) -> bool:
    if not segments:
        return False
    ev = _squash(evidence)
    for seg in segments:
        if ev in _squash(seg.get("text", "")):
            return seg.get("avg_logprob", 0.0) < LOW_LOGPROB or seg.get("no_speech_prob", 0.0) > HIGH_NO_SPEECH
    return False


def _minutes(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def _to_int(v) -> int | None:
    if v in (None, ""):
        return None
    m = re.search(r"\d+", key(str(v)))
    return int(m.group()) if m else None


def reconcile(
    kind: str,
    llm: dict | None,
    norm: dict,
    transcript: str,
    rec_date: date,
    segments: list[dict] | None = None,
    defaults: dict | None = None,
) -> dict:
    """Merge the LLM and normalizer readings into one candidate per field.

    Returns {"fields": {name: {value, status, candidates, evidence, span, flags, source}}, "summary": {...}}.
    `value` is None when the worker must pick one of `candidates`.
    """
    llm = llm or {}
    defaults = defaults or {}
    out: dict[str, dict] = {}

    for name in KIND_FIELDS[kind]:
        flags: list[str] = []
        raw = llm.get(name) or {}
        lv, ev = raw.get("value"), raw.get("evidence")
        if lv not in (None, ""):
            if not _grounded(ev, transcript):
                flags.append("UNGROUNDED")  # the quote is not in the transcript: never invent
                lv, ev = None, None
        else:
            lv = None
        n = norm.get(name)
        nv = n["value"] if n else None
        span = n["span"] if n else None
        candidates: list = []
        source = None

        if name in TIME_FIELDS:
            lc = parse_clock(lv) if lv is not None else None
        elif name in DATE_FIELDS:
            lc = parse_date(lv, rec_date) if lv is not None else None
        elif name in MONEY_FIELDS:
            lc = parse_money(lv) if lv is not None else None
        elif name in INT_FIELDS:
            lc = _to_int(lv)
        else:
            lc = lv if lv is not None else None

        if name in TIME_FIELDS or name in DATE_FIELDS or name in MONEY_FIELDS:
            if lc is None and nv is None:
                value, status = None, "red"
            elif lc is not None and nv is not None:
                if lc == nv:
                    candidates = [lc]
                    value = lc
                    status = "green" if n["status"] == "stated" else "amber"
                    if status == "amber":
                        flags.append(n["status"].upper())
                    source = "both"
                else:
                    candidates = [lc, nv]
                    value, status = None, "amber"
                    flags.append("READERS_DISAGREE")
            else:
                value = lc if lc is not None else nv
                candidates = [value]
                status = "amber"
                source = "llm" if lc is not None else "normalizer"
                flags.append("ONE_READER_ONLY")
                if n and n["status"] != "stated":
                    flags.append(n["status"].upper())
        else:
            value = lc
            status = "amber" if value not in (None, "") else "none"
            source = "llm" if value not in (None, "") else None
            candidates = [value] if value not in (None, "") else []

        if status == "green" and ev and _asr_low(ev, segments):
            status = "amber"
            flags.append("LOW_ASR_CONFIDENCE")

        if value is None and defaults.get(name) not in (None, ""):
            value = defaults[name]
            status = "amber"
            source = "default"
            flags.append("ASSUMED_CONFIRM")

        out[name] = {
            "value": value,
            "status": status,
            "candidates": candidates,
            "evidence": ev,
            "span": span,
            "flags": flags,
            "source": source,
        }

    _plausibility(out, rec_date)
    return {"fields": out, "summary": _summary(out)}


def _plausibility(out: dict, rec_date: date) -> None:
    s = out.get("start_time", {}).get("value")
    e = out.get("end_time", {}).get("value")
    br = _to_int(out.get("break_minutes", {}).get("value")) or 0
    if s and e:
        span = _minutes(e) - _minutes(s)
        if span <= 0:
            _mark(out["end_time"], "OVERNIGHT?")
        elif (span - br) / 60 > MAX_HOURS:
            _mark(out["end_time"], "HOURS_GT_16")
    amt = out.get("amount_paid", {}).get("value")
    if isinstance(amt, int) and amt > AMOUNT_FLAG:
        out["amount_paid"]["flags"].append("AMOUNT_HIGH")  # flag only: the worker decides
    for name in DATE_FIELDS:
        d_str = out.get(name, {}).get("value")
        if not d_str:
            continue
        d = date.fromisoformat(d_str)
        if d > rec_date:
            out[name]["flags"].append("FUTURE_DATE")
            out[name]["status"] = "red"
        elif (rec_date - d).days > LATE_DAYS:
            _mark(out[name], "LATE_ENTRY")


def _mark(field: dict, flag: str) -> None:
    field["flags"].append(flag)
    if field["status"] == "green":
        field["status"] = "amber"


def _summary(out: dict) -> dict:
    counts = {"green": 0, "amber": 0, "red": 0, "none": 0}
    for f in out.values():
        counts[f["status"]] += 1
    return counts
