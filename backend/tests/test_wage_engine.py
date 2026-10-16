"""Fixtures F1–F9 from planning/IMPLEMENTATION_HANDOFF.md §10.7 (Maharashtra Zone I unskilled)."""
from datetime import date, time, timedelta
from fractions import Fraction

import pytest

from app.money import fmt, to_decimal
from app.rates import RateContext, load_packs, resolve
from app.wage_engine import Payment, WorkDay, compute

PACKS = load_packs()
CTX = RateContext(sphere="state", state="Maharashtra", employment_sn=11, category="unskilled", zone="I")
D0 = date(2026, 10, 6)  # a Tuesday inside the Jul–Dec 2026 window
AS_OF = date(2026, 10, 16)


def day(d=D0, start="09:00", end="17:00", brk=0):
    h = lambda s: time.fromisoformat(s) if s else None
    return WorkDay(work_date=d, start=h(start), end=h(end), break_minutes=brk)


def pay(amount, d=D0):
    return Payment(pay_date=d, amount=Fraction(amount))


def run(days, payments=(), ctx=CTX, **kw):
    kw.setdefault("as_of", AS_OF)
    return compute(list(days), list(payments), ctx, PACKS, **kw)


def test_daily_rate_exact():
    rr = resolve(CTX, D0, PACKS)
    assert rr.daily_min == Fraction(22463, 26)
    assert fmt(rr.daily_min) == "863.96"
    assert fmt(rr.daily_min / 8) == "108.00"  # 107.995… rounds half-up


def test_f1_one_day_paid_700():
    r = run([day()], [pay(700)])
    assert r["ok"]
    assert r["totals"]["due_statutory"] == "863.96"
    assert r["totals"]["shortfall_statutory"] == "163.96"
    assert r["form_ii_heads"]["3a_below_minimum"] == "163.96"


def test_f2_nine_hours_with_ot():
    r = run([day(start="09:00", end="19:00", brk=60)])
    assert r["days"][0]["hours"] == "9.00"
    assert r["days"][0]["ot_hours"] == "1.00"
    assert r["totals"]["due_statutory"] == "1079.95"


def test_f3_partial_day():
    r = run([day(start="09:00", end="13:00")])
    assert r["totals"]["due_statutory"] == "431.98"
    assert "PARTIAL_DAY" in r["days"][0]["flags"]


def test_f4_unpaid_day_is_head_3d():
    r = run([day()], [])
    assert r["totals"]["shortfall_statutory"] == "863.96"
    assert r["form_ii_heads"]["3d_days_unpaid"] == "863.96"
    assert r["form_ii_heads"]["3d_unpaid_dates"] == [D0.isoformat()]


def test_f5_thirteen_days_exact_rounding():
    days = [day(D0 + timedelta(days=i), "09:00", "19:00", 60) for i in range(13)]
    r = run(days, [pay(2000), pay(2500, D0 + timedelta(days=7))])
    # exact 14039.375 -> half-up 14039.38 (a float/Decimal-division bug gives .37)
    assert r["totals"]["due_statutory"] == "14039.38"
    assert r["totals"]["paid_total"] == "4500.00"
    assert r["totals"]["shortfall_statutory"] == "9539.38"
    assert r["totals"]["claim_estimate"] == "9539.38"


def test_f6_out_of_window_shows_no_amount():
    r = run([day(date(2027, 1, 5))])
    assert not r["ok"]
    assert r["totals"] is None
    assert [e["code"] for e in r["errors"]] == ["RATE_OUT_OF_WINDOW"]


def test_f7_zone_unconfirmed():
    ctx = RateContext(sphere="state", state="Maharashtra", employment_sn=11, category="unskilled", zone=None)
    r = run([day()], ctx=ctx)
    assert not r["ok"] and r["totals"] is None
    assert r["errors"][0]["code"] == "ZONE_UNCONFIRMED"


def test_f8_agreed_rate_above_minimum():
    r = run([day(start="09:00", end="19:00", brk=60)], agreed_daily=1000)
    assert r["days"][0]["basis_contractual"] == "1000.00"
    assert r["totals"]["due_contractual"] == "1250.00"
    assert r["totals"]["due_statutory"] == "1079.95"
    assert r["totals"]["claim_estimate"] == "1250.00"


def test_f9_weekly_late_payment():
    mon = date(2026, 10, 5)
    assert mon.weekday() == 0
    days = [day(mon + timedelta(days=i)) for i in range(6)]  # Mon–Sat, Sunday holiday
    total_due = Fraction(22463, 26) * 6
    r = run(days, [Payment(mon + timedelta(days=9), total_due)], wage_period="weekly")  # next Wed
    late = r["late_payments"]
    assert len(late) == 1
    assert late[0]["code"] == "LATE_PAYMENT"
    assert late[0]["due_date"] == "2026-10-10"  # Saturday
    assert late[0]["days_late"] == 4


@pytest.mark.parametrize("field,value,code", [
    ("category", None, "CATEGORY_UNKNOWN"),
    ("sphere", "unknown", "SPHERE_UNKNOWN"),
    ("piece_rated", True, "PIECE_RATE_UNSUPPORTED"),
])
def test_context_errors_block_amounts(field, value, code):
    ctx = RateContext(**{**CTX.__dict__, field: value})
    r = run([day()], ctx=ctx)
    assert r["totals"] is None and r["errors"][0]["code"] == code


def test_no_confirmed_days():
    r = run([])
    assert r["errors"][0]["code"] == "NO_CONFIRMED_DAYS"


def test_highly_skilled_uses_skilled_rate_in_maharashtra():
    ctx = RateContext(**{**CTX.__dict__, "category": "highly_skilled"})
    assert resolve(ctx, D0, PACKS).daily_min == Fraction(25058, 26)


def test_hours_not_recorded_counts_normal_day():
    r = run([day(start=None, end=None)])
    assert "HOURS_NOT_RECORDED" in r["days"][0]["flags"]
    assert r["totals"]["due_statutory"] == "863.96"


def test_central_sphere_daily_rate():
    ctx = RateContext(sphere="central", state=None, employment_sn=None, category="unskilled", zone="A")
    r = run([day()], ctx=ctx)
    assert r["totals"]["due_statutory"] == "840.00"


def test_rounding_helper_half_up():
    assert str(to_decimal(Fraction(14039375, 1000))) == "14039.38"
    assert str(to_decimal(Fraction(-5, 1000))) == "-0.01"
