from datetime import date

from app.normalize import normalize
from app.reconcile import reconcile

REC = date(2026, 10, 16)
T = "सकाळी नऊ वाजता कामावर गेलो आणि संध्याकाळी सात वाजता सुटलो. ठेकेदार ने पाँच सौ रुपये दिए"
EMPTY = {"value": None, "evidence": None}


def _llm(**fields):
    names = ("work_date", "start_time", "end_time", "break_minutes", "worked", "site", "contractor_name",
             "contractor_phone", "principal_employer", "work_type", "agreed_rate", "coworkers_present",
             "incidents", "notes", "amount_paid", "payment_date")
    return {k: fields.get(k, EMPTY) for k in names}


def _run(llm, text=T, segments=None, defaults=None, kind="workday"):
    return reconcile(kind, llm, normalize(text, REC), text, REC, segments=segments, defaults=defaults)["fields"]


def test_both_readers_agree_and_stated_is_green():
    f = _run(_llm(start_time={"value": "9:00 AM", "evidence": "सकाळी नऊ वाजता"}))
    assert f["start_time"]["status"] == "green"
    assert f["start_time"]["value"] == "09:00"
    assert f["start_time"]["source"] == "both"


def test_disagreement_is_amber_with_both_candidates():
    f = _run(_llm(end_time={"value": "5:00 PM", "evidence": "संध्याकाळी सात वाजता"}))
    assert f["end_time"]["status"] == "amber"
    assert f["end_time"]["value"] is None  # the worker must pick
    assert f["end_time"]["candidates"] == ["17:00", "19:00"]
    assert "READERS_DISAGREE" in f["end_time"]["flags"]


def test_ungrounded_evidence_is_dropped_and_flagged():
    f = _run(_llm(amount_paid={"value": 700, "evidence": "सात सौ रुपये"}), kind="payment")
    assert "UNGROUNDED" in f["amount_paid"]["flags"]
    assert f["amount_paid"]["value"] == 500  # only the normalizer's reading survives
    assert f["amount_paid"]["status"] == "amber"


def test_nobody_found_it_is_red():
    empty = reconcile("workday", _llm(), {}, "काहीच नाही", REC)["fields"]
    assert empty["start_time"]["status"] == "red"
    assert empty["end_time"]["status"] == "red"
    assert empty["work_date"]["status"] == "red"


def test_low_asr_confidence_downgrades_green():
    seg = [{"text": T, "avg_logprob": -1.4, "no_speech_prob": 0.1}]
    f = _run(_llm(start_time={"value": "9:00 AM", "evidence": "सकाळी नऊ वाजता"}), segments=seg)
    assert f["start_time"]["status"] == "amber"
    assert "LOW_ASR_CONFIDENCE" in f["start_time"]["flags"]


def test_end_before_start_flags_overnight():
    text = "रात नऊ बजे से सुबह सात बजे तक"
    f = reconcile("workday", _llm(), normalize(text, REC), text, REC)["fields"]
    assert f["start_time"]["value"] == "21:00"
    assert "OVERNIGHT?" in f["end_time"]["flags"]


def test_more_than_16_hours_flagged():
    text = "सुबह चार बजे से रात नऊ बजे तक"
    f = reconcile("workday", _llm(), normalize(text, REC), text, REC)["fields"]
    assert "HOURS_GT_16" in f["end_time"]["flags"]


def test_future_date_is_red_and_old_entry_flagged_late():
    fut = reconcile("workday", _llm(work_date={"value": "2026-10-20", "evidence": "काम"}),
                    {}, "काम किया", REC)["fields"]
    assert fut["work_date"]["status"] == "red"
    assert "FUTURE_DATE" in fut["work_date"]["flags"]
    late = reconcile("workday", _llm(work_date={"value": "2026-09-01", "evidence": "काम"}),
                     {}, "काम किया", REC)["fields"]
    assert "LATE_ENTRY" in late["work_date"]["flags"]


def test_default_break_fills_only_missing_and_is_amber():
    f = _run(_llm(), defaults={"break_minutes": 60})
    assert f["break_minutes"]["value"] == 60
    assert f["break_minutes"]["status"] == "amber"
    assert "ASSUMED_CONFIRM" in f["break_minutes"]["flags"]


def test_no_default_means_no_value():
    assert _run(_llm())["break_minutes"]["value"] is None


def test_amount_above_5000_is_flagged_only():
    text = "ठेकेदार ने दस हजार रुपये दिए"
    f = reconcile("payment", _llm(amount_paid={"value": "10000", "evidence": "दस हजार रुपये"}),
                  normalize(text, REC), text, REC)["fields"]
    assert f["amount_paid"]["value"] == 10000
    assert "AMOUNT_HIGH" in f["amount_paid"]["flags"]
