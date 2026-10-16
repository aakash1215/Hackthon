"""Deterministic wage engine (pure functions, exact rational arithmetic).

The LLM never computes. Every amount here comes from confirmed inputs and a
rate pack with provenance. On a blocking error no amount is produced.

Per day (Code on Wages (Central) Rules 2026 r.3/r.5 convention; s.14 OT):
    daily_min = monthly_total / divisor            (divisor 26, assumption for MH)
    hours     = (end - start) - break
    normal    = min(hours, 8);  ot = max(0, hours - 8)
    basis     = max(daily_min, agreed_daily) if an agreed rate is known
    due       = basis * normal/8 + ot * (basis/8) * 2
"""
from __future__ import annotations

import calendar
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from fractions import Fraction

from .money import fmt, parse_amount
from .rates import RateContext, RateError, RatePack, check_context, resolve

WAGE_PERIODS = ("daily", "weekly", "fortnightly", "monthly", "unknown")


@dataclass
class WorkDay:
    work_date: date
    start: time | None = None
    end: time | None = None
    break_minutes: int = 0
    entry_id: str | None = None


@dataclass
class Payment:
    pay_date: date
    amount: Fraction
    entry_id: str | None = None
    deductions: list[dict] = field(default_factory=list)  # [{amount, reason}] as worker-reported


def _minutes(t: time) -> int:
    return t.hour * 60 + t.minute


def _day_hours(d: WorkDay) -> tuple[Fraction | None, list[str]]:
    flags: list[str] = []
    if d.start is None or d.end is None:
        return None, ["HOURS_NOT_RECORDED"]
    span = _minutes(d.end) - _minutes(d.start)
    if span <= 0:
        span += 24 * 60
        flags.append("OVERNIGHT")
    worked = span - (d.break_minutes or 0)
    if worked < 0:
        flags.append("INVALID_HOURS")
        worked = 0
    return Fraction(worked, 60), flags


# ---------------------------------------------------------------- s.17 periods
def _period(d: date, wage_period: str, weekly_holiday: int) -> tuple[date, date, date]:
    """Return (period_start, period_end, due_date) for a worked day."""
    if wage_period == "daily":
        return d, d, d
    if wage_period == "weekly":
        # Week closes on the weekly holiday; due on the last working day before it.
        ahead = (weekly_holiday - d.weekday()) % 7
        holiday = d + timedelta(days=ahead)
        return holiday - timedelta(days=6), holiday, holiday - timedelta(days=1)
    if wage_period == "fortnightly":
        last = calendar.monthrange(d.year, d.month)[1]
        if d.day <= 15:
            start, end = d.replace(day=1), d.replace(day=15)
        else:
            start, end = d.replace(day=16), d.replace(day=last)
        return start, end, end + timedelta(days=2)
    if wage_period == "monthly":
        last = calendar.monthrange(d.year, d.month)[1]
        nxt = (d.replace(day=last) + timedelta(days=1))
        # s.17: before the expiry of the 7th day of the succeeding month.
        return d.replace(day=1), d.replace(day=last), nxt.replace(day=7)
    raise ValueError(wage_period)


def _allocate_fifo(buckets: list[dict], payments: list[Payment]) -> None:
    """Allocate payments in date order to buckets in order. Mutates buckets.

    Each bucket needs 'amount' (Fraction) and gets 'allocated', 'paid_on'
    (date it became fully covered) and 'paid_by_due' if it has 'due_date'.
    """
    for b in buckets:
        b["allocated"] = Fraction(0)
        b["paid_on"] = None
        b["paid_by_due"] = Fraction(0)
    queue = [[p.pay_date, Fraction(p.amount)] for p in sorted(payments, key=lambda p: p.pay_date)]
    i = 0
    for b in buckets:
        while b["allocated"] < b["amount"] and i < len(queue):
            pdate, left = queue[i]
            take = min(left, b["amount"] - b["allocated"])
            b["allocated"] += take
            if "due_date" in b and pdate <= b["due_date"]:
                b["paid_by_due"] += take
            queue[i][1] -= take
            if b["allocated"] >= b["amount"]:
                b["paid_on"] = pdate
            if queue[i][1] == 0:
                i += 1


# ---------------------------------------------------------------------- main
def compute(
    days: list[WorkDay],
    payments: list[Payment],
    ctx: RateContext,
    packs: list[RatePack],
    agreed_daily=None,
    wage_period: str = "unknown",
    weekly_holiday: int = 6,  # Monday=0 … Sunday=6
    as_of: date | None = None,
) -> dict:
    as_of = as_of or date.today()
    agreed = parse_amount(agreed_daily) if agreed_daily not in (None, "") else None
    payments = [Payment(p.pay_date, parse_amount(p.amount), p.entry_id, p.deductions) for p in payments]
    if wage_period not in WAGE_PERIODS:
        wage_period = "unknown"

    result: dict = {
        "ok": False,
        "errors": [],
        "flags": [],
        "days": [],
        "totals": None,
        "form_ii_heads": None,
        "late_payments": [],
        "not_computed": [
            {"head": "3(b)", "label": "Weekly rest-day wages", "reason": "authority decides"},
            {"head": "—", "label": "Bonus", "reason": "authority decides"},
            {"head": "s.45", "label": "Compensation (up to 10x)", "reason": "authority decides"},
        ],
        "assumptions": [],
        "provenance": None,
        "rate_context": ctx.__dict__,
        "agreed_daily": fmt(agreed) if agreed is not None else None,
        "wage_period": wage_period,
    }

    if not days:
        result["errors"].append({"code": "NO_CONFIRMED_DAYS"})
        return result
    try:
        check_context(ctx)
    except RateError as e:
        result["errors"].append({"code": e.code, "detail": e.detail})
        return result

    seen: set[date] = set()
    computed = []
    packs_used: dict[str, RatePack] = {}
    for d in sorted(days, key=lambda x: x.work_date):
        row: dict = {"date": d.work_date.isoformat(), "entry_id": d.entry_id, "flags": []}
        if d.work_date in seen:
            row["flags"].append("DUPLICATE_DATE")
        seen.add(d.work_date)
        try:
            rr = resolve(ctx, d.work_date, packs)
        except RateError as e:
            row["error"] = e.code
            result["errors"].append({"code": e.code, "date": row["date"], "detail": e.detail})
            result["days"].append(row)
            continue
        packs_used[rr.pack.pack_id] = rr.pack
        nh = Fraction(rr.pack.normal_hours)
        mult = Fraction(rr.pack.ot_multiplier)
        hours, hflags = _day_hours(d)
        row["flags"] += hflags
        if hours is None:  # worker said "full day" but no times: normal day, no OT
            normal, ot = nh, Fraction(0)
        else:
            normal, ot = min(hours, nh), max(Fraction(0), hours - nh)
            if hours < nh:
                row["flags"].append("PARTIAL_DAY")

        def due_for(basis: Fraction) -> tuple[Fraction, Fraction]:
            normal_part = basis * normal / nh
            ot_part = ot * (basis / nh) * mult
            return normal_part, ot_part

        s_norm, s_ot = due_for(rr.daily_min)
        row.update({
            "start": d.start.strftime("%H:%M") if d.start else None,
            "end": d.end.strftime("%H:%M") if d.end else None,
            "break_minutes": d.break_minutes,
            "hours": fmt(hours) if hours is not None else None,
            "normal_hours": fmt(normal),
            "ot_hours": fmt(ot),
            "daily_min": fmt(rr.daily_min),
            "hourly_min": fmt(rr.daily_min / nh),
            "due_statutory": fmt(s_norm + s_ot),
            "pack_id": rr.pack.pack_id,
            "formula": (
                f"{fmt(rr.daily_min)} x {fmt(normal)}/{rr.pack.normal_hours}"
                + (f" + {fmt(ot)} x {fmt(rr.daily_min / nh)} x {rr.pack.ot_multiplier}" if ot else "")
            ),
        })
        c = {"row": row, "s_norm": s_norm, "s_ot": s_ot, "s_due": s_norm + s_ot, "date": d.work_date}
        if agreed is not None:
            basis = max(rr.daily_min, agreed)
            c_norm, c_ot = due_for(basis)
            c["c_due"] = c_norm + c_ot
            row["basis_contractual"] = fmt(basis)
            row["due_contractual"] = fmt(c["c_due"])
        computed.append(c)
        result["days"].append(row)

    if not computed:
        return result  # every day failed: errors already listed, no amounts

    if any(r.get("error") for r in result["days"]):
        result["flags"].append("PARTIAL_COMPARISON")
        result["assumptions"].append("Some days have no applicable rate and are excluded; payments are not split by day.")

    due_stat = sum((c["s_due"] for c in computed), Fraction(0))
    paid = sum((p.amount for p in payments), Fraction(0))
    short_stat = max(Fraction(0), due_stat - paid)
    totals = {
        "days_counted": len(computed),
        "due_statutory": fmt(due_stat),
        "paid_total": fmt(paid),
        "shortfall_statutory": fmt(short_stat),
        "due_contractual": None,
        "shortfall_contractual": None,
    }
    estimate = short_stat
    if agreed is not None:
        due_con = sum((c["c_due"] for c in computed), Fraction(0))
        short_con = max(Fraction(0), due_con - paid)
        totals["due_contractual"] = fmt(due_con)
        totals["shortfall_contractual"] = fmt(short_con)
        estimate = max(estimate, short_con)
    totals["claim_estimate"] = fmt(estimate)
    totals["claim_estimate_label"] = "estimate"
    result["totals"] = totals

    # ---- Form II heads (statutory track, payments allocated FIFO to days)
    buckets = [{"amount": c["s_due"], "c": c} for c in computed]
    _allocate_fifo(buckets, payments)
    head_a = head_c = head_d = Fraction(0)
    unpaid_days = []
    for b in buckets:
        short = b["amount"] - b["allocated"]
        if short <= 0:
            continue
        if b["allocated"] == 0:
            head_d += short
            unpaid_days.append(b["c"]["date"].isoformat())
        else:
            ot_part = min(short, b["c"]["s_ot"])
            head_c += ot_part
            head_a += short - ot_part
    deductions = [
        {"amount": fmt(parse_amount(x["amount"])), "reason": x.get("reason"), "payment_entry": p.entry_id}
        for p in payments for x in (p.deductions or []) if x.get("amount") not in (None, "")
    ]
    heads = {
        "3a_below_minimum": fmt(head_a),
        "3c_overtime_unpaid": fmt(head_c),
        "3d_days_unpaid": fmt(head_d),
        "3d_unpaid_dates": unpaid_days,
        "3e_deductions_reported": deductions,
        "3e_deductions_total": fmt(sum((parse_amount(x["amount"]) for x in deductions), Fraction(0))),
    }
    if agreed is not None:
        heads["agreed_rate_difference"] = fmt(
            max(Fraction(0), sum((c["c_due"] for c in computed), Fraction(0)) - due_stat))
        heads["agreed_rate_difference_note"] = "Contractual difference above the statutory minimum (not a Form II statutory head)."
    result["form_ii_heads"] = heads
    result["assumptions"].append("Payments are allocated to the earliest unpaid days first (FIFO).")
    if any("PARTIAL_DAY" in c["row"]["flags"] for c in computed):
        result["assumptions"].append("Partial days are pro-rated; a paralegal should check whether full-day rules apply.")

    # ---- s.17 late-payment flags
    if wage_period != "unknown":
        periods: dict[date, dict] = {}
        for c in computed:
            p_start, p_end, due = _period(c["date"], wage_period, weekly_holiday)
            per = periods.setdefault(p_end, {"start": p_start, "end": p_end, "due_date": due,
                                             "amount": Fraction(0)})
            per["amount"] += c["c_due"] if agreed is not None else c["s_due"]
        plist = [periods[k] for k in sorted(periods)]
        _allocate_fifo(plist, payments)
        for per in plist:
            status = None
            days_late = None
            if per["paid_on"] is not None and per["paid_on"] > per["due_date"]:
                status = "LATE_PAYMENT"
                days_late = (per["paid_on"] - per["due_date"]).days
            elif per["paid_on"] is None and as_of > per["due_date"]:
                status = "UNPAID_PAST_DUE"
                days_late = (as_of - per["due_date"]).days
            if status:
                result["late_payments"].append({
                    "code": status,
                    "period_start": per["start"].isoformat(),
                    "period_end": per["end"].isoformat(),
                    "due_date": per["due_date"].isoformat(),
                    "paid_on": per["paid_on"].isoformat() if per["paid_on"] else None,
                    "days_late": days_late,
                    "amount_due": fmt(per["amount"]),
                    "paid_by_due": fmt(per["paid_by_due"]),
                })
        if result["late_payments"]:
            result["flags"].append("LATE_PAYMENT")

    pack = next(iter(packs_used.values()))
    result["provenance"] = [p.provenance() for p in packs_used.values()]
    stale = all(as_of > p.effective_to for p in packs_used.values())
    if stale:
        result["flags"].append("RATES_MAY_BE_OUTDATED")
    if pack.conversion_status.startswith("ASSUMED"):
        result["assumptions"].append(
            f"Daily rate = monthly / {pack.daily_divisor}; normal day {pack.normal_hours} h (assumed for this state; verify).")
    result["ok"] = True
    return result


def parse_time(s: str | None) -> time | None:
    if not s:
        return None
    return datetime.strptime(s, "%H:%M").time()
