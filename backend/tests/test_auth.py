"""PIN login (UI/ O4 + A1): salted hash only, rate-limited, no PIN in the chain."""
import pytest

from app import auth, db
from tests.test_entries_api import client


@pytest.fixture(autouse=True)
def _reset_fails():
    auth._fails.clear()
    yield
    auth._fails.clear()


def _worker(wid="w1", name="सुनीता"):
    client.post("/api/workers", json={"id": wid, "display_name": name, "language": "mr"})


def test_directory_lists_workers_and_wins_over_worker_route():
    _worker()
    r = client.get("/api/workers/directory").json()
    assert r["items"][0] == {"id": "w1", "display_name": "सुनीता", "has_pin": False, "initial": "स"}


def test_set_pin_then_login():
    _worker()
    assert client.post("/api/workers/w1/pin", json={"pin": "12a4"}).status_code == 422
    assert client.post("/api/workers/w1/pin", json={"pin": "1234"}).json() == {"ok": True}
    with db.read() as c:
        stored = c.execute("SELECT pin_hash FROM worker_pins WHERE worker_id='w1'").fetchone()[0]
        payloads = " ".join(r[0] for r in c.execute("SELECT payload_json FROM events"))
    assert stored.startswith("pbkdf2_sha256$") and "1234" not in stored and "1234" not in payloads
    ok = client.post("/api/login", json={"worker_id": "w1", "pin": "1234"}).json()
    assert ok["worker"]["id"] == "w1" and ok["needs_pin"] is False
    assert client.post("/api/workers/directory").status_code in (404, 405)  # read-only route
    # changing the PIN needs the old one
    assert client.post("/api/workers/w1/pin", json={"pin": "9999"}).json()["detail"] == "OLD_PIN_REQUIRED"
    assert client.post("/api/workers/w1/pin", json={"pin": "9999", "old_pin": "1234"}).json() == {"ok": True}


def test_wrong_pin_locks_after_five_tries():
    _worker()
    client.post("/api/workers/w1/pin", json={"pin": "1234"})
    for left in (4, 3, 2, 1):
        assert client.post("/api/login", json={"worker_id": "w1", "pin": "0000"}).json()["detail"] == f"WRONG_PIN:{left}"
    assert client.post("/api/login", json={"worker_id": "w1", "pin": "0000"}).status_code == 401
    r = client.post("/api/login", json={"worker_id": "w1", "pin": "1234"})
    assert r.status_code == 429 and r.json()["detail"].startswith("LOCKED:")  # even the right PIN waits
    with db.read() as c:
        assert c.execute("SELECT COUNT(*) FROM events WHERE type='LOGIN_FAILED'").fetchone()[0] == 5


def test_old_account_without_pin_must_set_one():
    _worker()
    r = client.post("/api/login", json={"worker_id": "w1"}).json()
    assert r["needs_pin"] is True
    assert client.post("/api/login", json={"worker_id": "nobody", "pin": "1234"}).status_code == 404
