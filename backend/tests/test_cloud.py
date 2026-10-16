"""Optional ChatGPT engine: used only when configured AND asked for; any failure falls back to local.
No network: the HTTP layer is stubbed."""
import dataclasses
import json
import shutil

import pytest
from fastapi.testclient import TestClient

from app import api, asr, cloud, extract
from app.contracts import KIND_FIELDS
from app.main import app

client = TestClient(app)


class FakeResp:
    def __init__(self, status=200, body=None, content=b""):
        self.status_code, self._body, self.content = status, body, content

    def json(self):
        return self._body


@pytest.fixture
def keyed(monkeypatch):
    s = dataclasses.replace(cloud.settings, chat_api_key="test-key")
    monkeypatch.setattr(cloud, "settings", s)
    monkeypatch.setattr(api, "settings", dataclasses.replace(api.settings, chat_api_key="test-key"))
    return s


@pytest.fixture
def unkeyed(monkeypatch):
    monkeypatch.setattr(cloud, "settings", dataclasses.replace(cloud.settings, chat_api_key=""))
    monkeypatch.setattr(api, "settings", dataclasses.replace(api.settings, chat_api_key=""))


def _null_fields(kind):
    return {n: {"value": None, "evidence": None} for n in KIND_FIELDS[kind]}


def test_wanted_needs_key_and_choice(keyed, monkeypatch):
    assert cloud.wanted("cloud")
    assert not cloud.wanted("local") and not cloud.wanted(None)
    monkeypatch.setattr(cloud, "settings", dataclasses.replace(keyed, chat_api_key=""))
    assert not cloud.wanted("cloud")


def test_extract_uses_cloud_when_asked(keyed, monkeypatch):
    out = _null_fields("payment")
    seen = {}

    def fake_post(path, timeout, **kw):
        seen["path"], seen["body"] = path, kw["json"]
        return FakeResp(body={"choices": [{"message": {"content": json.dumps(out)}}]})

    monkeypatch.setattr(cloud, "_post", fake_post)
    assert extract.extract("payment", "आज पाँच सौ दिए", "2026-10-16", engine="cloud") == out
    assert seen["path"] == "/chat/completions"
    assert seen["body"]["temperature"] == 0
    assert seen["body"]["response_format"]["json_schema"]["schema"] == extract.json_schema_for("payment")


def test_extract_falls_back_to_local(keyed, monkeypatch):
    def down(*a, **k):
        raise cloud.CloudUnavailable("CLOUD_HTTP_429")

    out = _null_fields("payment")
    local_body = {"choices": [{"message": {"content": json.dumps(out)}}]}
    monkeypatch.setattr(cloud, "_post", down)
    monkeypatch.setattr(extract.httpx, "post", lambda url, **kw: FakeResp(body=local_body))
    assert extract.extract("payment", "आज पाँच सौ दिए", "2026-10-16", engine="cloud") == out


def test_local_choice_never_calls_cloud(keyed, monkeypatch):
    def boom(*a, **k):
        raise AssertionError("cloud called")

    monkeypatch.setattr(cloud, "_post", boom)
    monkeypatch.setattr(asr, "_transcribe_local", lambda wav, lang: {"language": "hi", "duration": 1.0, "text": "x",
                                                                     "segments": []})
    assert asr.transcribe_wav(None, "hi", engine="local")["engine"].startswith("local:")


def test_cloud_asr_shape_and_fallback(keyed, monkeypatch, tmp_path):
    wav = tmp_path / "16k.wav"
    wav.write_bytes(b"RIFF")
    body = {"text": " आज पाँच सौ दिए ", "language": "hindi", "duration": 3.2,
            "segments": [{"start": 0, "end": 3.2, "text": " आज पाँच सौ दिए", "avg_logprob": -0.21,
                          "no_speech_prob": 0.01}]}
    monkeypatch.setattr(cloud, "_post", lambda path, timeout, **kw: FakeResp(body=body))
    r = asr.transcribe_wav(wav, "hi", engine="cloud")
    assert r["text"] == "आज पाँच सौ दिए" and r["language"] == "hi" and r["engine"] == "cloud:whisper-1"
    assert r["segments"][0]["avg_logprob"] == -0.21

    def down(*a, **k):
        raise cloud.CloudUnavailable("CLOUD_ConnectError")

    monkeypatch.setattr(cloud, "_post", down)
    monkeypatch.setattr(asr, "_transcribe_local", lambda w, lang: {"language": "hi", "duration": 3.2, "text": "local",
                                                                   "segments": []})
    r = asr.transcribe_wav(wav, "hi", engine="cloud")
    assert r["text"] == "local" and r["engine"].startswith("local:")


def test_tts_endpoint(keyed, monkeypatch):
    monkeypatch.setattr(cloud, "tts", lambda text, lang: b"ID3mp3")
    r = client.post("/api/tts", json={"text": "आपका हिसाब सेव हो गया", "lang": "hi"})
    assert r.status_code == 200 and r.headers["content-type"] == "audio/mpeg" and r.content == b"ID3mp3"
    assert client.post("/api/tts", json={"text": "  "}).status_code == 422


def test_tts_endpoint_off_without_key(unkeyed):
    assert client.post("/api/tts", json={"text": "नमस्ते"}).json()["detail"] == "CLOUD_NOT_CONFIGURED"


def test_entry_engine_reaches_models(monkeypatch):
    seen = {}

    def fake_wav(src, dst):
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        return dst

    def fake_asr(wav, language, engine=None):
        seen["asr"] = engine
        return {"language": "hi", "duration": 2.0, "text": "आज पाँच सौ दिए", "segments": [], "engine": "cloud:x"}

    def fake_extract(kind, transcript, rec_date, context=None, timeout=300, engine=None):
        seen["llm"] = engine
        return _null_fields(kind)

    monkeypatch.setattr(asr, "to_wav16k", fake_wav)
    monkeypatch.setattr(asr, "transcribe_wav", fake_asr)
    monkeypatch.setattr(extract, "extract", fake_extract)
    client.post("/api/workers", json={"id": "w_cloud", "language": "hi", "consent_keep_audio": True})
    r = client.post("/api/entries", data={"kind": "payment", "worker_id": "w_cloud", "engine": "cloud"},
                    files={"audio": ("n.webm", b"bytes" * 40, "audio/webm")})
    assert r.status_code == 200, r.text
    api.process_entry(r.json()["entry_id"])
    assert seen == {"asr": "cloud", "llm": "cloud"}
