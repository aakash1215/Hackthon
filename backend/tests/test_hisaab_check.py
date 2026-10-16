"""Hisaab check: deterministic differences between a settlement statement and the ledger."""
from app.hisaab_check import compare

ENGINE = {
    "ok": True,
    "totals": {"due_statutory": "11232.00"},
    "days": [{"date": f"2026-10-{d:02d}", "daily_min": "863.96", "ot_hours": "1.00" if d == 2 else "0.00"}
             for d in range(1, 14)],
}
DAYS13 = [f"2026-10-{d:02d}" for d in range(1, 14)]


def codes(out):
    return [i["code"] for i in out["items"]]


def test_demo_case_12_days_600_minus_2000():
    out = compare({"days_counted": 12, "rate_per_day": 600, "deductions": 2000}, DAYS13, 0, ENGINE)
    assert codes(out) == ["DAYS_DIFF", "RATE_BELOW_MIN", "OT_NOT_COUNTED", "DEDUCTION_DISPUTED"]
    days, rate, ot, ded = out["items"]
    assert days["thekedar"] == "12" and days["record"] == "13" and days["severity"] == "urgent"
    assert rate["diff"] == "263.96"
    assert ot["record"] == "1.00" and ot["dates"] == ["2026-10-02"]
    assert ded["thekedar"] == "-2000.00" and ded["record"] is None and ded["severity"] == "ask"
    assert out["thekedar_total"] == "5200.00" and out["thekedar_total_basis"] == "days_x_rate"
    assert out["record_total"] == "11232.00"


def test_no_differences_when_everything_matches():
    eng = {**ENGINE, "days": [{**d, "ot_hours": "0.00", "daily_min": "500.00"} for d in ENGINE["days"]]}
    out = compare({"days_counted": 13, "rate_per_day": 600, "paid_now": 1000}, DAYS13, 1000, eng)
    assert out["count"] == 0


def test_paid_diff_and_stated_gross():
    out = compare({"gross_amount": 9000, "paid_now": 4500}, DAYS13, 2500, None)
    assert codes(out) == ["PAID_DIFF"]
    assert out["items"][0]["diff"] == "2000.00"
    assert out["thekedar_total"] == "9000.00" and out["thekedar_total_basis"] == "stated_gross"
    assert out["record_total"] is None  # engine not available → no amount, never a guess


def test_gross_above_days_times_rate_counts_as_including_ot():
    out = compare({"days_counted": 13, "rate_per_day": 900, "gross_amount": 12000}, DAYS13, 0, ENGINE)
    assert "OT_NOT_COUNTED" not in codes(out)


def test_more_days_claimed_is_ask_not_urgent():
    out = compare({"days_counted": 14}, DAYS13, 0, None)
    assert out["items"][0]["severity"] == "ask"
