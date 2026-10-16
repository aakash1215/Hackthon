"""Background processing: one entry at a time, on the hub, independent of the phone's connection.

Why: on the CPU tier ASR + LLM take 20–80 s per note. Running that inside the phone's HTTP request breaks
behind proxies/tunnels (~100 s limits) and when the phone sleeps, and every retry used to start another
parallel LLM call until the CPU drowned. Now an upload is queued right after save + hash; one worker thread
processes the queue in order; the phone only polls GET /api/entries/{id}. On hub start, every entry still
`saved` (never processed, or the model was down/timed out) is queued again.
"""
from __future__ import annotations

import logging
import queue
import threading

from . import db

log = logging.getLogger("apna_hisaab.processing")
_q: queue.Queue[str] = queue.Queue()
_state: dict[str, str] = {}  # entry_id → queued | running
_lock = threading.Lock()
_thread: threading.Thread | None = None


def enqueue(entry_id: str) -> str:
    """Queue an entry once; returns its processing state."""
    with _lock:
        if entry_id in _state:
            return _state[entry_id]
        _state[entry_id] = "queued"
    _q.put(entry_id)
    return "queued"


def active() -> bool:
    return bool(_thread and _thread.is_alive())


def status(entry_id: str) -> str | None:
    with _lock:
        return _state.get(entry_id)


def position(entry_id: str) -> int | None:
    """How many entries are ahead (0 = being processed now)."""
    with _lock:
        if entry_id not in _state:
            return None
        if _state[entry_id] == "running":
            return 0
        waiting = [e for e in list(_q.queue)]
        return (waiting.index(entry_id) + 1) if entry_id in waiting else None


def _worker() -> None:
    from fastapi import HTTPException

    from .api import process_entry

    while True:
        eid = _q.get()
        with _lock:
            _state[eid] = "running"
        try:
            res = process_entry(eid)
            log.info("processed %s → %s %s", eid, res.get("status"), res.get("error") or "")
        except HTTPException as e:  # already confirmed / deleted / refused: nothing to do
            log.info("skip %s: %s", eid, e.detail)
        except Exception:  # noqa: BLE001 — one bad entry must not stop the queue
            log.exception("processing %s failed", eid)
        finally:
            with _lock:
                _state.pop(eid, None)
            _q.task_done()


def pending_ids() -> list[str]:
    with db.read() as c:
        return [r["id"] for r in c.execute(
            "SELECT id FROM entries WHERE status='saved' AND audio_path != '' "
            "AND (error IS NULL OR error != 'CONSENT_REFUSED') ORDER BY server_ts DESC")]  # newest first


def start() -> None:
    """Start the single worker (idempotent) and re-queue unprocessed entries."""
    global _thread
    if _thread and _thread.is_alive():
        return
    _thread = threading.Thread(target=_worker, name="entry-processing", daemon=True)
    _thread.start()
    ids = pending_ids()
    for eid in ids:
        enqueue(eid)
    if ids:
        log.info("re-queued %d unprocessed entries", len(ids))
