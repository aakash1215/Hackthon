"""Login with a 4-digit PIN (UI/ O4 create, A1 "कौन इस्तेमाल कर रहा है").

The PIN is stored only as a salted PBKDF2-SHA256 hash. Wrong attempts are rate-limited per worker.
Scope, stated honestly: the PIN gates the app on a phone (who may open which worker's record). The hub API
itself is a LAN service without per-request auth in this hackathon build.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
import threading
import time

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from . import db, events

router = APIRouter()
ITERATIONS = 200_000
MAX_FAILS = 5
LOCK_SECONDS = 300
_fails: dict[str, tuple[int, float]] = {}  # worker_id → (consecutive fails, locked_until)
_lock = threading.Lock()
_TABLE = ("CREATE TABLE IF NOT EXISTS worker_pins (worker_id TEXT PRIMARY KEY REFERENCES workers(id), "
          "pin_hash TEXT NOT NULL, set_at TEXT NOT NULL)")


def hash_pin(pin: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", pin.encode(), bytes.fromhex(salt), ITERATIONS).hex()
    return f"pbkdf2_sha256${ITERATIONS}${salt}${h}"


def check_pin(pin: str, stored: str) -> bool:
    try:
        _, iters, salt, h = stored.split("$")
        got = hashlib.pbkdf2_hmac("sha256", pin.encode(), bytes.fromhex(salt), int(iters)).hex()
    except ValueError:
        return False
    return hmac.compare_digest(got, h)


def _valid(pin: str | None) -> bool:
    return bool(pin) and len(pin) == 4 and pin.isdigit()


def _stored(c, worker_id: str) -> str | None:
    c.execute(_TABLE)
    r = c.execute("SELECT pin_hash FROM worker_pins WHERE worker_id=?", (worker_id,)).fetchone()
    return r["pin_hash"] if r else None


def _profile(c, worker_id: str) -> dict:
    w = c.execute("SELECT * FROM workers WHERE id=?", (worker_id,)).fetchone()
    site = c.execute("SELECT * FROM sites WHERE worker_id=? ORDER BY created_at LIMIT 1", (worker_id,)).fetchone()
    parties = [dict(p) for p in c.execute("SELECT * FROM parties WHERE worker_id=?", (worker_id,))]
    return {"worker": dict(w), "site": dict(site) if site else None, "parties": parties}


@router.get("/api/workers/directory")
def directory():
    """Names for the A1 picker (most recent first)."""
    with db.write() as c:  # write(): creates worker_pins on first use
        c.execute(_TABLE)
        rows = c.execute("SELECT w.id, w.display_name, w.created_at, p.worker_id IS NOT NULL AS has_pin FROM workers w "
                         "LEFT JOIN worker_pins p ON p.worker_id = w.id ORDER BY w.created_at DESC LIMIT 12").fetchall()
    return {"items": [{"id": r["id"], "display_name": r["display_name"] or "बिना नाम", "has_pin": bool(r["has_pin"]),
                       "initial": (r["display_name"] or "?").strip()[:1]} for r in rows]}


class PinIn(BaseModel):
    pin: str
    old_pin: str | None = None


@router.post("/api/workers/{worker_id}/pin")
def set_pin(worker_id: str, body: PinIn):
    if not _valid(body.pin):
        raise HTTPException(422, "BAD_PIN")
    with db.write() as c:
        if not c.execute("SELECT 1 FROM workers WHERE id=?", (worker_id,)).fetchone():
            raise HTTPException(404, "WORKER_NOT_FOUND")
        old = _stored(c, worker_id)
        if old and not (body.old_pin and check_pin(body.old_pin, old)):
            raise HTTPException(403, "OLD_PIN_REQUIRED")
        c.execute("INSERT INTO worker_pins (worker_id, pin_hash, set_at) VALUES (?,?,datetime('now')) "
                  "ON CONFLICT(worker_id) DO UPDATE SET pin_hash=excluded.pin_hash, set_at=excluded.set_at",
                  (worker_id, hash_pin(body.pin)))
        events.append(c, "PIN_SET", {"worker_id": worker_id, "changed": bool(old)}, worker_id)  # never the PIN
    return {"ok": True}


class LoginIn(BaseModel):
    worker_id: str
    pin: str | None = None


@router.post("/api/login")
def login(body: LoginIn):
    """Verify the PIN and return the profile data. A worker who never set a PIN logs in and must set one now."""
    now = time.time()
    with _lock:
        fails, until = _fails.get(body.worker_id, (0, 0.0))
        if until > now:
            raise HTTPException(429, f"LOCKED:{int(until - now)}")
    with db.write() as c:
        if not c.execute("SELECT 1 FROM workers WHERE id=?", (body.worker_id,)).fetchone():
            raise HTTPException(404, "WORKER_NOT_FOUND")
        stored = _stored(c, body.worker_id)
    if stored and not (_valid(body.pin) and check_pin(body.pin, stored)):
        with _lock:
            fails += 1
            _fails[body.worker_id] = (0, now + LOCK_SECONDS) if fails >= MAX_FAILS else (fails, 0.0)
        with db.write() as c:  # its own transaction, so the failed attempt stays on the chain
            events.append(c, "LOGIN_FAILED", {"worker_id": body.worker_id, "attempt": fails}, body.worker_id)
        raise HTTPException(401, f"WRONG_PIN:{max(0, MAX_FAILS - fails)}")
    with _lock:
        _fails.pop(body.worker_id, None)
    with db.write() as c:
        events.append(c, "LOGIN", {"worker_id": body.worker_id, "had_pin": bool(stored)}, body.worker_id)
        return {**_profile(c, body.worker_id), "needs_pin": not stored}
