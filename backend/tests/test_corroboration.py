"""Corroboration levels per day (BUILD_PLAN §6, AC25): deterministic rules."""
from app.corroboration import at_site, compute_levels, distance_m

SITE = {"lat": 18.5204, "lon": 73.8567}
DAYS = ["2026-10-01", "2026-10-02", "2026-10-03"]


def test_worker_only_is_l1():
    lv = compute_levels(DAYS)
    assert all(v["level"] == 1 and v["signals"] == ["SELF"] for v in lv.values())
    assert lv["2026-10-01"]["label"]["en"] == "Worker's record"


def test_photo_that_day_is_l2_but_not_other_days():
    lv = compute_levels(DAYS, photos=[{"day": "2026-10-02", "lat": None, "lon": None, "acc": None, "ref": "p1"}])
    assert lv["2026-10-02"]["level"] == 2 and "PHOTO" in lv["2026-10-02"]["signals"]
    assert lv["2026-10-01"]["level"] == 1


def test_gps_at_site_needs_300m_and_good_accuracy():
    near = {"day": "2026-10-01", "lat": 18.5214, "lon": 73.8567, "acc": 20}  # ~110 m
    far = {"day": "2026-10-02", "lat": 18.5304, "lon": 73.8567, "acc": 20}  # ~1.1 km
    vague = {"day": "2026-10-03", "lat": 18.5205, "lon": 73.8567, "acc": 250}
    assert 100 < distance_m(SITE["lat"], SITE["lon"], near["lat"], near["lon"]) < 120
    lv = compute_levels(DAYS, site=SITE, fixes=[near, far, vague])
    assert lv["2026-10-01"]["level"] == 2 and "GPS_AT_SITE" in lv["2026-10-01"]["signals"]
    assert lv["2026-10-02"]["level"] == 1
    assert lv["2026-10-03"]["level"] == 1  # accuracy worse than 100 m does not count
    assert not at_site(near, None)  # no site point → no GPS signal


def test_coworker_raises_covered_days_to_l3():
    lv = compute_levels(DAYS, coworker=[{"dates": ["2026-10-01", "2026-10-03", "2026-09-30"], "ref": "c1"}])
    assert lv["2026-10-01"]["level"] == 3 and lv["2026-10-03"]["level"] == 3
    assert lv["2026-10-02"]["level"] == 1
    assert "2026-09-30" not in lv  # only confirmed workdays get a level


def test_thekedar_ack_covers_month_up_to_statement():
    lv = compute_levels(DAYS + ["2026-10-20"], thekedar=[
        {"rec_day": "2026-10-05", "days_counted": 3, "intent": "acknowledges", "ref": "t1"}])
    assert all(lv[d]["level"] == 3 and "THEKEDAR_ACK" in lv[d]["signals"] for d in DAYS)
    assert lv["2026-10-20"]["level"] == 1  # after the statement: not covered


def test_thekedar_counting_fewer_days_is_a_dispute_flag_not_an_ack():
    lv = compute_levels(DAYS, thekedar=[{"rec_day": "2026-10-05", "days_counted": 2, "intent": "promise_to_pay"}])
    for d in DAYS:
        assert lv[d]["level"] == 1
        assert lv[d]["flags"] == ["THEKEDAR_DISPUTES"]


def test_dispute_is_shown_alongside_other_evidence():
    lv = compute_levels(DAYS, coworker=[{"dates": DAYS}],
                        thekedar=[{"rec_day": "2026-10-03", "days_counted": None, "intent": "disputes_days"}])
    assert lv["2026-10-01"]["level"] == 3  # the co-worker still counts
    assert "THEKEDAR_DISPUTES" in lv["2026-10-01"]["flags"]  # and the dispute is never hidden


def test_rate_dispute_or_unclear_stance_changes_nothing():
    lv = compute_levels(DAYS, thekedar=[{"rec_day": "2026-10-03", "days_counted": None, "intent": "disputes_rate"},
                                        {"rec_day": "2026-10-03", "days_counted": None, "intent": "other"}])
    assert all(v["level"] == 1 and not v["flags"] for v in lv.values())


def test_deterministic():
    kw = dict(site=SITE, photos=[{"day": "2026-10-02", "lat": 18.5204, "lon": 73.8568, "acc": 10}],
              coworker=[{"dates": ["2026-10-03"]}])
    assert compute_levels(DAYS, **kw) == compute_levels(list(reversed(DAYS)), **kw)
