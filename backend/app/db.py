"""SQLite store in WAL mode. Tables from Handoff §10.3 plus BUILD_PLAN §5 columns.

Writes go through `write()`: one process-wide lock plus BEGIN IMMEDIATE, so the event
chain's read-last-hash-then-insert step can't interleave. Never call a model inside
`write()`; ASR and LLM calls are slow and must not hold the lock.
"""
from __future__ import annotations

import sqlite3
import threading
from collections.abc import Iterator
from contextlib import contextmanager

from .config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS workers (
  id TEXT PRIMARY KEY,
  display_name TEXT,
  language TEXT NOT NULL DEFAULT 'mr' CHECK (language IN ('hi','mr')),
  category TEXT CHECK (category IN ('unskilled','semi_skilled','skilled','highly_skilled')),
  default_break_min INTEGER,
  consent_keep_audio INTEGER NOT NULL DEFAULT 0,
  gps_opt_in INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sites (
  id TEXT PRIMARY KEY,
  worker_id TEXT NOT NULL REFERENCES workers(id),
  name TEXT, landmark TEXT, city TEXT, state TEXT,
  sphere TEXT CHECK (sphere IN ('state','central','unknown')),
  zone TEXT CHECK (zone IN ('I','II','III','A','B','C')),
  zone_confirmed INTEGER NOT NULL DEFAULT 0,
  principal_employer TEXT, maharera_no TEXT,
  employment_sn INTEGER DEFAULT 11,
  wage_period TEXT NOT NULL DEFAULT 'unknown',
  site_lat REAL, site_lon REAL, site_gps_accuracy_m REAL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS parties (
  id TEXT PRIMARY KEY,
  worker_id TEXT NOT NULL REFERENCES workers(id),
  site_id TEXT REFERENCES sites(id),
  role TEXT NOT NULL CHECK (role IN ('mukadam','contractor','subcontractor','principal_employer')),
  name TEXT, phone TEXT,
  source TEXT NOT NULL DEFAULT 'stated' CHECK (source IN ('stated','site_board'))
);
CREATE TABLE IF NOT EXISTS entries (
  id TEXT PRIMARY KEY,
  worker_id TEXT NOT NULL REFERENCES workers(id),
  site_id TEXT REFERENCES sites(id),
  kind TEXT NOT NULL CHECK (kind IN ('workday','payment','hisaab_statement','coworker_confirm')),
  speaker TEXT NOT NULL DEFAULT 'worker' CHECK (speaker IN ('worker','thekedar','coworker')),
  language TEXT NOT NULL DEFAULT 'mr',
  audio_path TEXT NOT NULL,
  audio_sha256 TEXT NOT NULL,
  client_sha256 TEXT,
  hash_match INTEGER,
  client_ts TEXT,
  server_ts TEXT NOT NULL,
  lat REAL, lon REAL, gps_accuracy_m REAL, gps_ts TEXT,
  status TEXT NOT NULL DEFAULT 'saved' CHECK (status IN ('saved','processed','confirmed','deleted')),
  transcript TEXT,
  asr_meta TEXT,
  extraction TEXT,
  reconciled TEXT,
  confirmed TEXT,
  confirmed_at TEXT,
  processed_tier TEXT NOT NULL DEFAULT 'server',
  notice_played INTEGER NOT NULL DEFAULT 0,
  linked_day_ids TEXT,
  error TEXT
);
CREATE INDEX IF NOT EXISTS entries_worker_kind ON entries(worker_id, kind, status);
CREATE TABLE IF NOT EXISTS evidence (
  id TEXT PRIMARY KEY,
  worker_id TEXT NOT NULL REFERENCES workers(id),
  entry_id TEXT REFERENCES entries(id),
  kind TEXT NOT NULL CHECK (kind IN ('photo','payment_proof','site_board','witness_audio')),
  path TEXT NOT NULL,
  sha256 TEXT NOT NULL,
  caption TEXT,
  consent INTEGER NOT NULL DEFAULT 0,
  lat REAL, lon REAL, gps_accuracy_m REAL, taken_ts TEXT,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS events (
  seq INTEGER PRIMARY KEY,
  worker_id TEXT,
  ts_server TEXT NOT NULL,
  ts_client TEXT,
  type TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  prev_hash TEXT NOT NULL,
  hash TEXT NOT NULL
);
"""

_write_lock = threading.RLock()


def connect() -> sqlite3.Connection:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(
        settings.data_dir / "apna.db", timeout=30, isolation_level=None, check_same_thread=False
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    conn = connect()
    try:
        conn.executescript(SCHEMA)
    finally:
        conn.close()


@contextmanager
def read() -> Iterator[sqlite3.Connection]:
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def write() -> Iterator[sqlite3.Connection]:
    with _write_lock:
        conn = connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            yield conn
            conn.execute("COMMIT")
        except BaseException:
            conn.execute("ROLLBACK")
            raise
        finally:
            conn.close()
