"""Append-only, hash-chained event log (Handoff §10.9).

hash = sha256(prev_hash + canonical(event without hash)); genesis prev_hash = 64 zeros.
Events are never updated. A changed payload breaks the chain at that seq, and
verify() reports where.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone

GENESIS = "0" * 64


def canonical(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def chain_hash(prev_hash: str, body: dict) -> str:
    return hashlib.sha256(prev_hash.encode() + canonical(body)).hexdigest()


def short(h: str) -> str:
    """Human chain-head code, e.g. 7F3A-9C21-B4."""
    h = h.upper()
    return f"{h[0:4]}-{h[4:8]}-{h[8:10]}"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def append(
    conn: sqlite3.Connection,
    type_: str,
    payload: dict,
    worker_id: str | None = None,
    ts_client: str | None = None,
) -> dict:
    """Append one event. Call inside db.write() so the read of the last hash and the insert are atomic."""
    last = conn.execute("SELECT seq, hash FROM events ORDER BY seq DESC LIMIT 1").fetchone()
    seq = last["seq"] + 1 if last else 1
    prev = last["hash"] if last else GENESIS
    ts_server = _now()
    body = {
        "seq": seq,
        "type": type_,
        "worker_id": worker_id,
        "ts_server": ts_server,
        "ts_client": ts_client,
        "payload": payload,
        "prev_hash": prev,
    }
    h = chain_hash(prev, body)
    conn.execute(
        "INSERT INTO events (seq, worker_id, ts_server, ts_client, type, payload_json, prev_hash, hash) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (seq, worker_id, ts_server, ts_client, type_, canonical(payload).decode("utf-8"), prev, h),
    )
    return {"seq": seq, "type": type_, "hash": h}


def head(conn: sqlite3.Connection) -> dict | None:
    row = conn.execute("SELECT seq, hash FROM events ORDER BY seq DESC LIMIT 1").fetchone()
    if row is None:
        return None
    return {"seq": row["seq"], "hash": row["hash"], "short": short(row["hash"])}


def verify(conn: sqlite3.Connection) -> dict:
    """Recompute every hash. Returns {ok, events, head} or {ok: False, broken_at_seq, events}."""
    prev = GENESIS
    count = 0
    for row in conn.execute("SELECT * FROM events ORDER BY seq"):
        body = {
            "seq": row["seq"],
            "type": row["type"],
            "worker_id": row["worker_id"],
            "ts_server": row["ts_server"],
            "ts_client": row["ts_client"],
            "payload": json.loads(row["payload_json"]),
            "prev_hash": row["prev_hash"],
        }
        if row["prev_hash"] != prev or chain_hash(prev, body) != row["hash"]:
            return {"ok": False, "broken_at_seq": row["seq"], "events": count}
        prev = row["hash"]
        count += 1
    return {"ok": True, "events": count, "head": head_from(prev, count)}


def head_from(h: str, count: int) -> dict | None:
    if count == 0:
        return None
    return {"hash": h, "short": short(h)}
