"""Voice typing for form fields: hash + save before ASR, filler cleanup, consent honoured, ASR-down degrade."""
import hashlib
import shutil

import pytest
from fastapi.testclient import TestClient

from app import asr
from app.api import clean_dictation
from app.config import settings
from app.main import app

client = TestClient(app)
AUDIO = b"short-clip" * 40


@pytest.mark.parametrize("raw,field,want", [
    ("मेरा नाम सुनीता है।", "name", "सुनीता"),
    ("  राजू कुमार  ", "name", "राजू कुमार"),
    ("माझं नाव सुरेश आहे", "name", "सुरेश"),
    ("ठेकेदार का नाम कैलाश है", "name", "कैलाश"),
    ("बस स्टैंड के पीछे।", "text", "बस स्टैंड के पीछे"),
    ("", "name", ""),
])
def test_clean_dictation(raw, field, want):
    assert clean_dictation(raw, field) == want


@pytest.fixture
def stub_asr(monkeypatch):
    state = {"text": "मेरा नाम सुनीता है", "error": None}

    def fake_wav(src, dst):
        assert src.read_bytes() == AUDIO  # original saved before transcoding
        shutil.copyfile(src, dst)
        return dst

    def fake_transcribe(wav, language):
        if state["error"]:
            raise asr.ASRUnavailable(state["error"])
        state["language"] = language
        return {"text": state["text"]}

    monkeypatch.setattr(asr, "to_wav16k", fake_wav)
    monkeypatch.setattr(asr, "transcribe_wav", fake_transcribe)
    return state


def _post(**data):
    return client.post("/api/dictate", files={"audio": ("a.webm", AUDIO, "audio/webm")}, data=data)


def test_dictate_name_keeps_hashed_original(stub_asr):
    r = _post(language="hi", field="name")
    assert r.status_code == 200
    body = r.json()
    assert body["text"] == "सुनीता" and body["audio_sha256"] == hashlib.sha256(AUDIO).hexdigest()
    kept = list((settings.data_dir / "media" / "dictation").glob("*/original.webm"))
    assert len(kept) == 1 and not list(kept[0].parent.glob("16k.wav"))


def test_dictate_without_consent_drops_audio(stub_asr):
    r = _post(language="en", field="text", keep_audio="false")
    assert r.status_code == 200 and stub_asr["language"] == "auto"
    assert not list((settings.data_dir / "media" / "dictation").glob("*/*"))


def test_dictate_asr_down(stub_asr):
    stub_asr["error"] = "ASR_MODEL_LOAD_FAILED"
    assert _post(field="name").status_code == 503
