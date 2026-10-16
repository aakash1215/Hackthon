"""Runtime configuration from .env (repo root). Model servers are config, never hardcoded.

Every service is optional: if the LLM, ASR, TTS or Telegram is unavailable the
app degrades (entries stay `saved`) instead of crashing.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(REPO_ROOT / ".env")


def _bool(name: str, default: bool) -> bool:
    v = os.getenv(name)
    if v is None or v.strip() == "":
        return default
    return v.strip().lower() in ("1", "true", "yes", "on")


def _path(v: str) -> Path:
    p = Path(v)
    return p if p.is_absolute() else REPO_ROOT / p


@dataclass(frozen=True)
class Settings:
    # LLM (llama-server, OpenAI-compatible API, open-weight model)
    llm_base_url: str
    llm_model: str
    # ASR (faster-whisper)
    asr_mode: str  # local | remote
    asr_url: str  # used when asr_mode == remote
    asr_model: str  # local path (relative to repo root) or HF id
    asr_device: str  # cpu | cuda
    asr_compute_type: str  # int8 | int8_float16 | float16
    # Optional services
    tts_enabled: bool
    telegram_bot_token: str
    telegram_bot_username: str
    demo_mode: bool
    # Storage and server
    data_dir: Path
    host: str
    port: int
    cert_file: Path
    key_file: Path

    @property
    def tier(self) -> str:
        """`gpu` when ASR runs on CUDA or is remote (cloud GPU), else `cpu`."""
        return "gpu" if self.asr_device == "cuda" or self.asr_mode == "remote" else "cpu"

    @property
    def asr_model_path(self) -> str:
        """Local directory if it exists, otherwise the value as given (HF id / size name)."""
        p = _path(self.asr_model)
        return str(p) if p.exists() else self.asr_model

    @property
    def telegram_configured(self) -> bool:
        return bool(self.telegram_bot_token)


def load_settings() -> Settings:
    return Settings(
        llm_base_url=os.getenv("LLM_BASE_URL", "http://127.0.0.1:8080/v1").rstrip("/"),
        llm_model=os.getenv("LLM_MODEL", "Qwen3-1.7B-Q4_K_M"),
        asr_mode=os.getenv("ASR_MODE", "local").strip().lower(),
        asr_url=os.getenv("ASR_URL", "").rstrip("/"),
        asr_model=os.getenv("ASR_MODEL", "models/asr/faster-whisper-small"),
        asr_device=os.getenv("ASR_DEVICE", "cpu").strip().lower(),
        asr_compute_type=os.getenv("ASR_COMPUTE_TYPE", "int8"),
        tts_enabled=_bool("TTS_ENABLED", False),
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", "").strip(),
        telegram_bot_username=os.getenv("TELEGRAM_BOT_USERNAME", "").strip().lstrip("@"),
        demo_mode=_bool("DEMO_MODE", True),
        data_dir=_path(os.getenv("DATA_DIR", "data")),
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8443")),
        cert_file=_path(os.getenv("CERT_FILE", "certs/cert.pem")),
        key_file=_path(os.getenv("KEY_FILE", "certs/key.pem")),
    )


settings = load_settings()
