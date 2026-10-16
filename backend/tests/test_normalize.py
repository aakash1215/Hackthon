from datetime import date

from app.normalize import normalize, parse_clock, parse_date, parse_money

REC = date(2026, 10, 16)


def _t(text):
    return normalize(text, REC)


def test_hindi_time_range_stated():
    r = _t("आज सुबह नौ बजे से शाम सात बजे तक काम किया।")
    assert r["start_time"] == {"value": "09:00", "status": "stated", "span": "सुबह नौ बजे"}
    assert r["end_time"] == {"value": "19:00", "status": "stated", "span": "शाम सात बजे"}


def test_bare_range_9_to_7_is_inferred_09_to_19():
    r = _t("9 से 7 काम किया")
    assert r["start_time"]["value"] == "09:00" and r["start_time"]["status"] == "inferred"
    assert r["end_time"]["value"] == "19:00" and r["end_time"]["status"] == "inferred"


def test_part_of_day_with_bare_end_hour():
    r = _t("सुबह 9 से 7 बजे")
    assert r["start_time"]["value"] == "09:00"
    assert r["end_time"]["value"] == "19:00"


def test_fraction_pauney_in_evening():
    assert _t("शाम पौने आठ बजे")["start_time"]["value"] == "19:45"


def test_fraction_sadhe_is_half_hour():
    assert _t("साढ़े नऊ बजे")["start_time"]["value"] == "09:30"


def test_marathi_times_with_vajta():
    r = _t("सकाळी नऊ वाजता कामावर गेलो आणि संध्याकाळी सहा वाजता सुटलो.")
    assert r["start_time"]["value"] == "09:00" and r["start_time"]["status"] == "stated"
    assert r["end_time"]["value"] == "18:00" and r["end_time"]["status"] == "stated"


def test_money_compounds_and_symbols():
    assert _t("ठेकेदार ने आज पाँच सौ रुपये दिए")["amount_paid"]["value"] == 500
    assert _t("दोन हजार पाचशे रुपये")["amount_paid"]["value"] == 2500
    assert _t("₹2,000 दिए")["amount_paid"]["value"] == 2000
    assert _t("रु 500")["amount_paid"]["value"] == 500
    assert _t("पांचशे रुपये")["amount_paid"]["value"] == 500


def test_no_currency_no_amount():
    assert "amount_paid" not in _t("पाँच सौ दिए")


def test_dates():
    assert _t("आज काम किया")["work_date"] == {"value": "2026-10-16", "status": "stated", "span": "आज"}
    assert _t("काल कामावर")["work_date"]["value"] == "2026-10-15"  # Marathi काल = yesterday
    assert _t("कल काम किया")["work_date"]["status"] == "ambiguous"  # Hindi कल: amber, worker is asked
    assert _t("परसों पैसे")["work_date"]["status"] == "ambiguous"


def test_nth_of_month_most_recent_past():
    assert _t("13 तारीख को काम")["work_date"] == {"value": "2026-10-13", "status": "inferred", "span": "13 तारीख"}
    assert normalize("13 तारीख", date(2026, 10, 10))["work_date"]["value"] == "2026-09-13"


def test_devanagari_digits():
    assert _t("९ बजे से ७ बजे")["start_time"]["value"] == "09:00"


def test_parse_llm_clock_values():
    assert parse_clock("9:00 AM") == "09:00"
    assert parse_clock("5:00 PM") == "17:00"
    assert parse_clock("12:00 AM") == "00:00"
    assert parse_clock("19:30") == "19:30"
    assert parse_clock("शाम सात बजे") == "19:00"
    assert parse_clock("nonsense") is None


def test_parse_llm_money_and_date_values():
    assert parse_money("5000 रुपये") == 5000
    assert parse_money("2,000") == 2000
    assert parse_money(700) == 700
    assert parse_money("पाँच सौ") == 500
    assert parse_date("2026-10-13", REC) == "2026-10-13"
    assert parse_date("काल", REC) == "2026-10-15"
    assert parse_date("garbage", REC) is None
