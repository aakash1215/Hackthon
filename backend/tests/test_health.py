from fastapi.testclient import TestClient

from app.main import app


def test_health_degrades_without_model_servers():
    r = TestClient(app).get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["tier"] in ("cpu", "gpu")
    assert set(body) >= {"llm", "asr", "tts", "telegram"}
    assert "token" not in str(body["telegram"]).lower()
