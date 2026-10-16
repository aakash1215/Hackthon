"""ASR: faster-whisper locally, or a remote model server (ASR_MODE=remote, POST /internal/asr).

The original bytes are hashed and saved before this module is called. Here we only transcode
(ffmpeg → 16 kHz mono WAV) and transcribe. Nothing is written to the DB from this module.
"""
from __future__ import annotations

import logging
import os
import subprocess
import threading
from pathlib import Path

import httpx

from . import cloud
from .config import REPO_ROOT, settings

log = logging.getLogger("apna_hisaab.asr")


class ASRUnavailable(Exception):
    """Raised when ASR can't run. Callers keep the entry `saved` and return the code."""


_model = None
_model_lock = threading.Lock()


def _cuda_dll_dirs() -> None:
    """Windows: the nvidia-cublas-cu12 / nvidia-cudnn-cu12 wheels keep their DLLs in site-packages/nvidia/*/bin,
    which CTranslate2 does not search. Put them on the DLL path before the model loads."""
    if os.name != "nt":
        return
    import importlib.util

    spec = importlib.util.find_spec("nvidia")
    dirs = [b for base in ((spec.submodule_search_locations or []) if spec else []) for b in Path(base).glob("*/bin")]
    # llama.cpp's CUDA build ships cuBLAS 12 (cudart-llama-bin zip); reuse it instead of a second 400 MB copy.
    llama_cuda = REPO_ROOT / "models" / "llama.cpp" / "cuda"
    if llama_cuda.is_dir():
        dirs.append(llama_cuda)
    for b in dirs:
        os.add_dll_directory(str(b))
        os.environ["PATH"] = f"{b}{os.pathsep}{os.environ.get('PATH', '')}"


def _load():
    global _model
    with _model_lock:
        if _model is None:
            from faster_whisper import WhisperModel  # heavy import, kept lazy so the app starts fast

            if settings.asr_device == "cuda":
                _cuda_dll_dirs()
                try:
                    _model = WhisperModel(settings.asr_model_path, device="cuda",
                                          compute_type=settings.asr_compute_type)
                    return _model
                except Exception as e:  # noqa: BLE001 — no CUDA libs / VRAM: degrade to CPU, don't crash
                    log.warning("ASR on CUDA failed (%s: %s); falling back to CPU int8", type(e).__name__, e)
            _model = WhisperModel(
                settings.asr_model_path,
                device="cpu",
                compute_type=settings.asr_compute_type if settings.asr_device == "cpu" else "int8",
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


def transcribe_wav(wav: Path, language: str, engine: str | None = None) -> dict:
    """language: 'hi' | 'mr' forces the language; 'auto' lets Whisper detect it (thekedar recordings).
    engine: 'cloud' tries the optional ChatGPT API first (when configured), then falls back to local.

    Returns {language, duration, text, segments:[{start,end,text,avg_logprob,no_speech_prob,words}], engine}.
    """
    if cloud.wanted(engine):
        try:
            return cloud.transcribe(wav, language)
        except cloud.CloudUnavailable as e:
            log.warning("cloud ASR failed (%s); using local ASR", e)
    return {"engine": f"local:{settings.asr_model}", **_transcribe_local(wav, language)}


def _transcribe_local(wav: Path, language: str) -> dict:
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
