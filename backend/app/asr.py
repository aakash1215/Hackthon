"""ASR: faster-whisper locally, or a remote model server (ASR_MODE=remote, POST /internal/asr).

The original bytes are hashed and saved before this module is called. Here we only transcode
(ffmpeg → 16 kHz mono WAV) and transcribe. Nothing is written to the DB from this module.
"""
from __future__ import annotations

import subprocess
import threading
from pathlib import Path

import httpx

from .config import settings


class ASRUnavailable(Exception):
    """Raised when ASR can't run. Callers keep the entry `saved` and return the code."""


_model = None
_model_lock = threading.Lock()


def _load():
    global _model
    with _model_lock:
        if _model is None:
            from faster_whisper import WhisperModel  # heavy import, kept lazy so the app starts fast

            _model = WhisperModel(
                settings.asr_model_path,
                device=settings.asr_device,
                compute_type=settings.asr_compute_type,
            )
    return _model


def to_wav16k(src: Path, dst: Path) -> Path:
    dst.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-ac", "1", "-ar", "16000", str(dst)],
        capture_output=True,
        timeout=180,
    )
    if r.returncode != 0 or not dst.exists():
        raise ASRUnavailable("TRANSCODE_FAILED: " + r.stderr.decode("utf-8", "ignore")[-200:])
    return dst


def transcribe_wav(wav: Path, language: str) -> dict:
    """language: 'hi' | 'mr' forces the language; 'auto' lets Whisper detect it (thekedar recordings).

    Returns {language, duration, text, segments:[{start,end,text,avg_logprob,no_speech_prob,words}]}.
    """
    if settings.asr_mode == "remote":
        if not settings.asr_url:
            raise ASRUnavailable("ASR_URL_NOT_SET")
        try:
            with wav.open("rb") as f:
                r = httpx.post(
                    f"{settings.asr_url}/internal/asr",
                    files={"audio": (wav.name, f, "audio/wav")},
                    data={"language": language},
                    timeout=600,
                )
            r.raise_for_status()
            return r.json()
        except httpx.HTTPError as e:
            raise ASRUnavailable(f"REMOTE_ASR_{type(e).__name__}") from e

    try:
        model = _load()
    except Exception as e:  # missing model dir, CUDA not present, etc.
        raise ASRUnavailable(f"ASR_MODEL_LOAD_FAILED: {type(e).__name__}: {e}") from e

    # Bounded decoding: on noisy/unclear audio the default temperature-fallback ladder and conditioning on
    # previous text made a 5 s clip loop for minutes on a 2-core CPU. One greedy pass, no word timestamps.
    segs, info = model.transcribe(
        str(wav),
        language=None if language == "auto" else language,
        beam_size=settings.asr_beam_size,
        temperature=0.0,
        condition_on_previous_text=False,
        word_timestamps=False,
        vad_filter=True,
    )
    segments = []
    for s in segs:
        segments.append({
            "start": round(s.start, 2),
            "end": round(s.end, 2),
            "text": s.text.strip(),
            "avg_logprob": round(s.avg_logprob, 3),
            "no_speech_prob": round(s.no_speech_prob, 3),
            "words": [
                {"word": w.word.strip(), "start": round(w.start, 2), "end": round(w.end, 2),
                 "probability": round(w.probability, 3)}
                for w in (s.words or [])
            ],
        })
    return {
        "language": info.language,
        "duration": round(info.duration, 2),
        "text": " ".join(s["text"] for s in segments).strip(),
        "segments": segments,
    }
