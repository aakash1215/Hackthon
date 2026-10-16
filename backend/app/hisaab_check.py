"""Hisaab check (BUILD_PLAN P3): compare a worker-confirmed settlement statement with the ledger.

Deterministic. Inputs are worker-confirmed statement values, the confirmed ledger and the wage
engine's output; no model output reaches this module. Codes:

  DAYS_DIFF           thekedar's day count differs from the confirmed workdays
  RATE_BELOW_MIN      his daily rate is below the statutory daily minimum the engine used
  OT_NOT_COUNTED      the record has overtime hours that his figure does not include
  DEDUCTION_DISPUTED  he deducts an advance/other amount (the worker should check it)
  PAID_DIFF           what he says was paid differs from the payments in the record
"""
from __future__ import annotations

from fractions import Fraction

from .money import fmt, parse_amount


def _num(v) -> Fraction | None:
    if v in (None, ""):
        return None
    try:
        return parse_amount(v)
    except (TypeError, ValueError, ArithmeticError):
        return None


def _count(x: Fraction) -> str:
    """Day counts read as whole numbers when they are whole ("12", not "12.00")."""
    return str(x.numerator) if x.denominator == 1 else fmt(x)


def compare(statement: dict, record_days: list[str], paid_total, engine: dict | None,
            record_deductions_noted: bool = False) -> dict:
    """Return {thekedar_total, thekedar_total_basis, record_total, items[], count}.

    statement: confirmed hisaab_statement fields (days_counted, rate_per_day, gross_amount, deductions,
    paid_now, balance_promised, promised_date). record_days: confirmed workday dates in the window.
    paid_total: confirmed payments in the window. engine: wage_engine.compute() output for the window.
    """
    days = _num(statement.get("days_counted"))
    rate = _num(statement.get("rate_per_day"))
    gross = _num(statement.get("gross_amount"))
    ded = _num(statement.get("deductions")) or Fraction(0)
    paid_now = _num(statement.get("paid_now"))
    paid_rec = _num(paid_total) or Fraction(0)
    n_rec = len(record_days)
    engine_ok = bool(engine and engine.get("ok"))
    rows = [r for r in (engine or {}).get("days", []) if not r.get("error")]

    items: list[dict] = []
    if days is not None and days != n_rec:
        items.append({
            "code": "DAYS_DIFF", "severity": "urgent" if days < n_rec else "ask",
            "thekedar": _count(days), "record": str(n_rec), "diff": _count(Fraction(n_rec) - days),
            "dates": list(record_days),
        })

    daily_min = min((_num(r["daily_min"]) for r in rows), default=None) if engine_ok else None
    if rate is not None and daily_min is not None and rate < daily_min:
        items.append({
            "code": "RATE_BELOW_MIN", "severity": "urgent",
            "thekedar": fmt(rate), "record": fmt(daily_min), "diff": fmt(daily_min - rate),
        })

    ot_hours = sum((_num(r.get("ot_hours")) or Fraction(0) for r in rows), Fraction(0)) if engine_ok else Fraction(0)
    his_gross = gross if gross is not None else (days * rate if days is not None and rate is not None else None)
    includes_ot = gross is not None and days is not None and rate is not None and gross > days * rate
    if ot_hours > 0 and not includes_ot:
        items.append({
            "code": "OT_NOT_COUNTED", "severity": "urgent",
            "thekedar": "0", "record": fmt(ot_hours), "unit": "hours",
            "dates": [r["date"] for r in rows if (_num(r.get("ot_hours")) or 0) > 0],
        })

    if ded > 0:
        items.append({
            "code": "DEDUCTION_DISPUTED", "severity": "ask",
            "thekedar": fmt(-ded), "record": None if not record_deductions_noted else "noted",
        })

    if paid_now is not None and paid_now != paid_rec:
        items.append({
            "code": "PAID_DIFF", "severity": "ask",
            "thekedar": fmt(paid_now), "record": fmt(paid_rec), "diff": fmt(paid_now - paid_rec),
        })

    his_total = his_gross - ded if his_gross is not None else None
    return {
        "thekedar_total": fmt(his_total) if his_total is not None else None,
        "thekedar_total_basis": None if his_gross is None else "stated_gross" if gross is not None else "days_x_rate",
        "record_total": (engine or {}).get("totals", {}).get("due_statutory") if engine_ok else None,
        "record_days": n_rec,
        "record_paid": fmt(paid_rec),
        "items": items,
        "count": len(items),
    }
