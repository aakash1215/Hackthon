"""P1 check with the real LLM (llama-server) and the real normalizer/reconciler, on text transcripts.

Audio-level Hindi/Marathi checks need real recordings (data/demo_clips/). This script runs the
text half of the pipeline on hi/mr sentences so the colour logic can be seen on real model output.

Run from backend/:  PYTHONIOENCODING=utf-8 uv run --no-project python ../scripts/p1_text_check.py
"""
import sys
import time
from datetime import date

sys.path.insert(0, ".")
from app import extract, normalize, reconcile  # noqa: E402

REC = date(2026, 10, 16)
CASES = [
    ("workday", "mr", "काल सकाळी नऊ वाजता कामावर गेलो आणि संध्याकाळी सहा वाजता सुटलो."),
    ("workday", "hi", "आज सुबह नौ बजे से शाम सात बजे तक काम किया। ठेकेदार ने कुछ नहीं दिया।"),
    ("payment", "hi", "ठेकेदार ने आज पाँच सौ रुपये cash में दिए"),
    ("payment", "mr", "मालकाने काल दोन हजार रुपये दिले, रोख"),
]

for kind, lang, text in CASES:
    t0 = time.time()
    norm = normalize.normalize(text, REC)
    try:
        llm = extract.extract(kind, text, REC.isoformat(), {"usual_break_minutes": 60})
        err = None
    except extract.LLMUnavailable as e:
        llm, err = None, str(e)
    dt = time.time() - t0
    rec = reconcile.reconcile(kind, llm, norm, text, REC, defaults={"break_minutes": 60} if kind == "workday" else None)
    print(f"\n[{kind} {lang}] {text}\n  llm {dt:.1f}s err={err}")
    for name, f in rec["fields"].items():
        if f["status"] == "none":
            continue
        print(f"  {name:14} {f['status']:6} value={f['value']!s:10} cands={f['candidates']} flags={f['flags']}")
    print("  summary", rec["summary"])
