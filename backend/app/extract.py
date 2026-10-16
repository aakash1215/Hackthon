"""LLM extraction via llama-server (open-weight model, JSON-schema output, temperature 0).

The model only copies facts and quotes evidence. It never computes. Its output goes through
reconcile.py, which checks grounding and compares it with the normalizer.
"""
from __future__ import annotations

import json

import httpx

from .config import settings
from .contracts import FEW_SHOT, KIND_FIELDS, SYSTEM_PROMPT, json_schema_for

_FEW_SHOT_DATE = "2026-10-16"


class LLMUnavailable(Exception):
    """Raised when llama-server is down, slow or returns something that isn't valid JSON."""


def _user_msg(kind: str, transcript: str, rec_date: str, context: dict | None) -> str:
    lines = [f"Kind: {kind}", f"Recording date (context, not a fact): {rec_date}"]
    if context:
        lines.append("Worker defaults (context, not facts): " + json.dumps(context, ensure_ascii=False))
    lines.append("Transcript:\n" + transcript)
    return "\n".join(lines)


def build_messages(kind: str, transcript: str, rec_date: str, context: dict | None) -> list[dict]:
    msgs: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
    for ex_transcript, ex_out in FEW_SHOT.get(kind, []):
        msgs.append({"role": "user", "content": _user_msg(kind, ex_transcript, _FEW_SHOT_DATE, None)})
        msgs.append({"role": "assistant", "content": json.dumps(ex_out, ensure_ascii=False)})
    msgs.append({"role": "user", "content": _user_msg(kind, transcript, rec_date, context)})
    return msgs


def extract(kind: str, transcript: str, rec_date: str, context: dict | None = None, timeout: float = 300) -> dict:
    """Return {field: {value, evidence}} for every field of `kind`. Raises LLMUnavailable."""
    if kind not in KIND_FIELDS:
        raise ValueError(f"unknown kind {kind}")
    body = {
        "model": settings.llm_model,
        "temperature": 0,
        "messages": build_messages(kind, transcript, rec_date, context),
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": kind, "schema": json_schema_for(kind)},
        },
        "chat_template_kwargs": {"enable_thinking": False},
    }
    try:
        r = httpx.post(f"{settings.llm_base_url}/chat/completions", json=body, timeout=timeout)
    except httpx.HTTPError as e:
        raise LLMUnavailable(f"LLM_{type(e).__name__}") from e
    if r.status_code != 200:
        raise LLMUnavailable(f"LLM_HTTP_{r.status_code}")
    try:
        out = json.loads(r.json()["choices"][0]["message"]["content"])
    except (KeyError, IndexError, ValueError, TypeError) as e:
        raise LLMUnavailable("LLM_BAD_JSON") from e
    if not isinstance(out, dict):
        raise LLMUnavailable("LLM_BAD_JSON")
    return out
