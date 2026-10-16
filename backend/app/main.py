"""Apna Hisaab hub: FastAPI serving /api/* and the built PWA from one HTTPS origin.

Run (from backend/):  uv run --no-project python -m app.main
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import agent, api, auth, db, evidence_api, processing, telegram_bot
from .config import REPO_ROOT, settings

log = logging.getLogger("apna_hisaab")
if not log.handlers:  # app logs (processing queue, Telegram) next to uvicorn's in the hub log
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("%(asctime)s %(name)s %(levelname)s: %(message)s", "%H:%M:%S"))
    log.addHandler(_h)
    log.setLevel(logging.INFO)
FRONTEND_DIST = REPO_ROOT / "frontend" / "dist"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    db.init_db()  # WAL SQLite; idempotent
    processing.start()  # one background worker for ASR + LLM; re-queues anything still `saved`
    if settings.telegram_configured:  # long polling in this event loop; retries quietly while offline
        telegram_bot.RUNTIME.start()
    yield
    await telegram_bot.RUNTIME.stop()


app = FastAPI(title="Apna Hisaab", version="0.1.0", lifespan=lifespan)
app.include_router(auth.router)  # first: /api/workers/directory must win over /api/workers/{id}
app.include_router(api.router)  # before the SPA catch-all below, so /api/* routes win
app.include_router(evidence_api.router)
app.include_router(telegram_bot.router)
app.include_router(agent.router)


async def _llm_status() -> dict:
    base = settings.llm_base_url.removesuffix("/v1")
    try:
        async with httpx.AsyncClient(timeout=1.5) as c:
            r = await c.get(f"{base}/health")
        return {"ok": r.status_code == 200, "url": settings.llm_base_url, "model": settings.llm_model}
    except httpx.HTTPError as e:
        return {"ok": False, "url": settings.llm_base_url, "model": settings.llm_model, "error": type(e).__name__}


async def _asr_status() -> dict:
    info = {"mode": settings.asr_mode, "model": settings.asr_model, "device": settings.asr_device}
    if settings.asr_mode == "remote":
        try:
            async with httpx.AsyncClient(timeout=1.5) as c:
                r = await c.get(f"{settings.asr_url}/api/health")
            return {**info, "ok": r.status_code == 200, "url": settings.asr_url}
        except httpx.HTTPError as e:
            return {**info, "ok": False, "url": settings.asr_url, "error": type(e).__name__}
    # A local CT2 directory must exist; a bare size name ("small") is fetched by faster-whisper.
    return {**info, "ok": Path(settings.asr_model_path).is_dir() or "/" not in settings.asr_model}


@app.get("/api/health")
async def health() -> dict:
    llm = await _llm_status()
    asr = await _asr_status()
    return {
        "ok": True,
        "tier": settings.tier,
        "demo_mode": settings.demo_mode,
        "llm": llm,
        "asr": asr,
        "tts": {"enabled": settings.tts_enabled},
        # Optional ChatGPT engine: only whether it can be offered (never the key).
        "cloud": {"configured": settings.cloud_configured, "llm_model": settings.chat_llm_model,
                  "asr_model": settings.chat_asr_model, "tts_model": settings.chat_tts_model},
        "telegram": {"configured": settings.telegram_configured, "bot": settings.telegram_bot_username or None,
                     "running": telegram_bot.RUNTIME.running},
    }


# --- PWA (built frontend) with SPA fallback; /api/* never falls back ---
if FRONTEND_DIST.is_dir():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    async def spa(path: str):
        if path.startswith("api/"):
            return JSONResponse({"error": "NOT_FOUND"}, status_code=404)
        f = (FRONTEND_DIST / path).resolve()
        if path and f.is_file() and f.is_relative_to(FRONTEND_DIST.resolve()):
            return FileResponse(f)
        return FileResponse(FRONTEND_DIST / "index.html")


def run() -> None:
    import uvicorn

    ssl = {}
    if settings.cert_file.exists() and settings.key_file.exists():
        ssl = {"ssl_certfile": str(settings.cert_file), "ssl_keyfile": str(settings.key_file)}
    else:
        log.warning("No certs at %s; serving plain HTTP (phone mic/SW need HTTPS)", settings.cert_file)
    uvicorn.run(app, host=settings.host, port=settings.port, **ssl)


if __name__ == "__main__":
    run()
