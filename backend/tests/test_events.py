import json

from app import db, events


def _chain(n=3):
    with db.write() as c:
        for i in range(n):
            events.append(c, "TEST", {"i": i, "name": "नमस्ते"}, worker_id="w1")


def test_genesis_and_chain_verifies():
    _chain(3)
    with db.read() as c:
        rows = c.execute("SELECT seq, prev_hash FROM events ORDER BY seq").fetchall()
        v = events.verify(c)
    assert rows[0]["prev_hash"] == events.GENESIS
    assert rows[1]["prev_hash"] != events.GENESIS
    assert v["ok"] is True and v["events"] == 3
    assert len(v["head"]["short"]) == 12  # e.g. 7F3A-9C21-B4


def test_empty_chain_verifies():
    with db.read() as c:
        assert events.verify(c) == {"ok": True, "events": 0, "head": None}


def test_tampered_payload_breaks_chain_at_that_seq():
    _chain(4)
    with db.write() as c:
        c.execute("UPDATE events SET payload_json=? WHERE seq=2", (json.dumps({"i": 99}),))
    with db.read() as c:
        v = events.verify(c)
    assert v == {"ok": False, "broken_at_seq": 2, "events": 1}


def test_rewritten_link_breaks_the_chain():
    _chain(3)
    with db.write() as c:
        c.execute("UPDATE events SET prev_hash=? WHERE seq=3", ("0" * 64,))
    with db.read() as c:
        assert events.verify(c)["ok"] is False


def test_short_code_format():
    assert events.short("7f3a9c21b4" + "0" * 54) == "7F3A-9C21-B4"
