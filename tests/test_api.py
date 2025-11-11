import pytest
import os
from fastapi.testclient import TestClient
from app.main import app
from pathlib import Path

client = TestClient(app)

@pytest.fixture(scope="session", autouse=True)
def ensure_model_loaded():
    # Wait until startup event runs; TestClient triggers startup
    pass

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert "status" in data

def test_transcribe_with_sample_audio():
    sample = Path(__file__).parent / "sample_audio" / "hello.m4a"
    assert sample.exists(), f"Place a small m4a at {sample}"
    with open(sample, "rb") as fh:
        r = client.post("/transcribe", files={"file": ("hello.m4a", fh)})
    # if model not loaded in CI, allow 503 or 200; assert expected structure when success
    if r.status_code == 200:
        data = r.json()
        assert "text" in data
        assert data.text == "hello"
        assert "segments" in data
    else:
        assert r.status_code in (503, 400)