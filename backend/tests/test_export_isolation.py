"""Two workers on one hub: each evidence file holds only that worker's photos, media and chain events."""
import io
import json
import zipfile

from fastapi.testclient import TestClient
from PIL import Image

from app import packet
from app.config import settings
from app.main import app

client = TestClient(app)


def _jpeg(color):
    b = io.BytesIO()
    Image.new("RGB", (40, 40), color).save(b, "JPEG")
    return b.getvalue()


def _worker(wid, color):
    client.post("/api/workers", json={"id": wid, "display_name": wid, "language": "hi", "category": "unskilled"}).raise_for_status()
    client.post("/api/sites", json={"worker_id": wid, "name": "S", "city": "पुणे", "state": "Maharashtra", "zone": "I"}).raise_for_status()
    r = client.post("/api/evidence/photo", files={"photo": ("p.jpg", _jpeg(color), "image/jpeg")},
                    data={"worker_id": wid, "kind": "site_board", "client_ts": "2026-10-10T10:00:00+05:30",
                          "lat": "18.5", "lon": "73.8"})
    r.raise_for_status()
    return r.json()["evidence_id"]


def test_packet_holds_only_own_data(monkeypatch):
    monkeypatch.setattr(packet, "_render_pdf", lambda html, pdf: "SKIPPED")
    ev = {"aaaaaaaaaaaa": _worker("aaaaaaaaaaaa", "red"), "bbbbbbbbbbbb": _worker("bbbbbbbbbbbb", "blue")}
    for wid, other in (("aaaaaaaaaaaa", "bbbbbbbbbbbb"), ("bbbbbbbbbbbb", "aaaaaaaaaaaa")):
        r = client.post("/api/export", json={"worker_id": wid, "date_from": "2026-10-01", "date_to": "2026-10-16"})
        assert r.status_code == 200
        z = zipfile.ZipFile(settings.data_dir / "exports" / r.json()["export_id"] / "bundle.zip")
        media = [n for n in z.namelist() if n.startswith("media/")]
        assert media and all(ev[wid] in n for n in media) and not any(ev[other] in n for n in media)
        chain = [json.loads(line) for line in z.read("chain/events.jsonl").decode().splitlines()]
        assert chain and {e["worker_id"] for e in chain} == {wid}
        assert ev[other] not in z.read("packet.html").decode("utf-8")
