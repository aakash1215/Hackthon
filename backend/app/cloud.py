"""Optional cloud engine: the ChatGPT API (closed model) for ASR, extraction and read-back TTS.

Off by default. It runs only when CHAT_API_KEY is set AND the worker picked "तेज़" in Settings
(the phone sends `engine=cloud`). The same rules hold as for the local models: the original bytes are
saved and hashed before this module is called; the LLM only extracts {value, evidence} under the same
JSON schema and reconcile.py still checks every evidence substring; code does all the arithmetic.
Every failure raises CloudUnavailable and the caller falls back to the local open-weight model.
"""
from __future__ import annotations

import hashlib
import json
import threading
from collections import OrderedDict
from pathlib import Path

import httpx

from .config import settings


class CloudUnavailable(Exception):
    pass


def wanted(engine: str | None) -> bool:
    return engine == "cloud" and settings.cloud_configured


def _post(path: str, timeout: float, **kw) -> httpx.Response:
    try:
        r = httpx.post(f"{settings.chat_base_url}{path}", headers={"Authorization": f"Bearer {settings.chat_api_key}"},
                       timeout=timeout, **kw)
    except httpx.HTTPError as e:
        raise CloudUnavailable(f"CLOUD_{type(e).__name__}") from e
    if r.status_code != 200:
        raise CloudUnavailable(f"CLOUD_HTTP_{r.status_code}")
    return r


_LANG = {"hindi": "hi", "marathi": "mr", "english": "en"}


def transcribe(wav: Path, language: str) -> dict:
    """Same shape as asr.transcribe_wav. whisper-1 returns segments; other models return text only."""
    model = settings.chat_asr_model
    verbose = model == "whisper-1"
    data = {"model": model, "response_format": "verbose_json" if verbose else "json", "temperature": "0"}
    if language in ("hi", "mr"):
        data["language"] = language
    with wav.open("rb") as f:
        r = _post("/audio/transcriptions", 300, files={"file": (wav.name, f, "audio/wav")}, data=data)
    try:
        j = r.json()
    except ValueError as e:
        raise CloudUnavailable("CLOUD_BAD_JSON") from e
    text = (j.get("text") or "").strip()
    duration = round(float(j.get("duration") or 0), 2)
    if verbose and j.get("segments"):
        segments = [{
            "start": round(s.get("start", 0), 2), "end": round(s.get("end", 0), 2),
            "text": (s.get("text") or "").strip(),
            "avg_logprob": round(s.get("avg_logprob", 0), 3), "no_speech_prob": round(s.get("no_speech_prob", 0), 3),
            "words": [],
        } for s in j["segments"]]
    else:
        segments = [{"start": 0.0, "end": duration, "text": text, "avg_logprob": 0.0, "no_speech_prob": 0.0,
                     "words": []}] if text else []
    lang = str(j.get("language") or (language if language in ("hi", "mr") else "auto")).lower()
    return {"language": _LANG.get(lang, lang), "duration": duration, "text": text, "segments": segments,
            "engine": f"cloud:{model}"}


def chat_json(name: str, messages: list[dict], schema: dict, timeout: float) -> dict:
    body = {
        "model": settings.chat_llm_model,
        "temperature": 0,
        "messages": messages,
        "response_format": {"type": "json_schema", "json_schema": {"name": name, "schema": schema, "strict": False}},
    }
    r = _post("/chat/completions", min(timeout, 90), json=body)
    try:
        out = json.loads(r.json()["choices"][0]["message"]["content"])
    except (KeyError, IndexError, ValueError, TypeError) as e:
        raise CloudUnavailable("CLOUD_BAD_JSON") from e
    if not isinstance(out, dict):
        raise CloudUnavailable("CLOUD_BAD_JSON")
    return out


# Read-back texts repeat (notices, fixed templates): keep the last clips in memory.
_tts_cache: OrderedDict[str, bytes] = OrderedDict()
_tts_lock = threading.Lock()

_TTS_STYLE = {
    "hi": "Speak in Hindi in a warm, calm, clear female voice, a little slowly.",
    "mr": "Speak in Marathi in a warm, calm, clear female voice, a little slowly.",
    "en": "Speak in Indian English in a warm, calm, clear female voice, a little slowly.",
}


def tts(text: str, lang: str = "hi") -> bytes:
    """MP3 of a code-filled template text, in a female voice (CHAT_TTS_VOICE, default 'coral')."""
    key = hashlib.sha256(f"{lang}|{settings.chat_tts_voice}|{text}".encode()).hexdigest()
    with _tts_lock:
        if key in _tts_cache:
            _tts_cache.move_to_end(key)
            return _tts_cache[key]
    body = {"model": settings.chat_tts_model, "voice": settings.chat_tts_voice, "input": text, "response_format": "mp3"}
    if settings.chat_tts_model not in ("tts-1", "tts-1-hd"):  # only gpt-4o-*-tts takes style instructions
        body["instructions"] = _TTS_STYLE.get(lang, _TTS_STYLE["hi"])
    audio = _post("/audio/speech", 60, json=body).content
    with _tts_lock:
        _tts_cache[key] = audio
        while len(_tts_cache) > 100:
            _tts_cache.popitem(last=False)
    return audio
