"""P0 smoke test: llama-server answers a JSON-schema-constrained request (thinking off).

Run from backend/:  uv run --no-project python ../scripts/smoke_llm.py
"""
import json
import sys
import time

import httpx

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")
from app.config import settings  # noqa: E402

FIELD = {
    "type": "object",
    "properties": {"value": {"type": ["string", "null"]}, "evidence": {"type": ["string", "null"]}},
    "required": ["value", "evidence"],
}
SCHEMA = {
    "type": "object",
    "properties": {"start_time": FIELD, "end_time": FIELD, "amount_paid": FIELD},
    "required": ["start_time", "end_time", "amount_paid"],
    "additionalProperties": False,
}
TRANSCRIPT = "आज सुबह नौ बजे से शाम सात बजे तक काम किया, ठेकेदार ने पाँच सौ रुपये दिए"

body = {
    "model": settings.llm_model,
    "temperature": 0,
    "messages": [
        {"role": "system", "content": "Extract fields from the transcript. evidence must be an exact substring of the "
                                      "transcript, else value and evidence are null. Do not compute anything."},
        {"role": "user", "content": TRANSCRIPT},
    ],
    "response_format": {"type": "json_schema", "json_schema": {"name": "workday", "schema": SCHEMA}},
    "chat_template_kwargs": {"enable_thinking": False},
}
t = time.time()
r = httpx.post(f"{settings.llm_base_url}/chat/completions", json=body, timeout=300)
r.raise_for_status()
out = json.loads(r.json()["choices"][0]["message"]["content"])
print(json.dumps(out, ensure_ascii=False, indent=1))
grounded = all(f["evidence"] is None or f["evidence"] in TRANSCRIPT for f in out.values())
print(f"{time.time() - t:.1f}s, schema keys ok={set(out) == set(SCHEMA['required'])}, evidence grounded={grounded}")
