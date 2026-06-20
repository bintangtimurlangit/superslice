"""Tests for opt-in auth and rate limiting."""
import pytest
from fastapi.testclient import TestClient

from app.core import security
from app.main import app
from app.services import slicing

client = TestClient(app)

_VALID_STL = ("cube.stl", b"solid x\nendsolid x\n", "application/octet-stream")
_VALID_FORM = {"layer_height": "0.2", "infill_density": "20", "wall_count": "3"}


def _mock_slicer(monkeypatch):
    monkeypatch.setattr(slicing, "run_slicer", lambda *a, **k: None)
    monkeypatch.setattr(
        slicing,
        "parse_gcode_statistics",
        lambda path, density: {
            "filament_length_mm": 1.0,
            "filament_volume_cm3": 1.0,
            "filament_weight_g": density,
            "print_time_seconds": 60,
            "print_time_formatted": "1m 0s",
        },
    )


def test_auth_disabled_by_default(monkeypatch):
    _mock_slicer(monkeypatch)
    resp = client.post("/slice", files={"file": _VALID_STL}, data=_VALID_FORM)
    assert resp.status_code == 200


def test_auth_rejects_without_key(monkeypatch):
    monkeypatch.setattr(security, "API_KEYS", ["s3cret"])
    resp = client.post("/slice", files={"file": _VALID_STL}, data=_VALID_FORM)
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "UNAUTHORIZED"


def test_auth_accepts_valid_key(monkeypatch):
    monkeypatch.setattr(security, "API_KEYS", ["s3cret"])
    _mock_slicer(monkeypatch)
    resp = client.post(
        "/slice",
        files={"file": _VALID_STL},
        data=_VALID_FORM,
        headers={"X-API-Key": "s3cret"},
    )
    assert resp.status_code == 200


def test_rate_limit_trips(monkeypatch):
    monkeypatch.setattr(security, "RATE_LIMIT_PER_MINUTE", 2)
    security._hits.clear()
    _mock_slicer(monkeypatch)

    for _ in range(2):
        ok = client.post("/slice", files={"file": _VALID_STL}, data=_VALID_FORM)
        assert ok.status_code == 200

    limited = client.post("/slice", files={"file": _VALID_STL}, data=_VALID_FORM)
    assert limited.status_code == 429
    assert limited.json()["error"]["code"] == "RATE_LIMITED"
    assert "Retry-After" in limited.headers
