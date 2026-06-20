"""Tests for build-volume fit and support detection."""
from fastapi.testclient import TestClient

from app.main import app
from app.services import slicing

client = TestClient(app)

_STL = ("model.stl", b"solid x\nendsolid x\n", "application/octet-stream")
_FORM = {"layer_height": "0.2", "infill_density": "20", "wall_count": "3"}


def _mock(monkeypatch, *, dims, supports):
    monkeypatch.setattr(slicing, "run_slicer", lambda *a, **k: None)
    monkeypatch.setattr(slicing, "get_model_dimensions", lambda p: dims)
    monkeypatch.setattr(slicing, "gcode_has_support_material", lambda p: supports)
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


def test_fits_build_volume_within_256(monkeypatch):
    _mock(monkeypatch, dims=(80.0, 80.0, 40.0), supports=False)
    body = client.post("/slice", files={"file": _STL}, data=_FORM).json()
    assert body["fits_build_volume"] is True
    assert body["build_volume_mm"] == {"x": 256.0, "y": 256.0, "z": 256.0}
    assert body["model_dimensions_mm"] == {"x": 80.0, "y": 80.0, "z": 40.0}


def test_oversized_model_flagged_not_rejected(monkeypatch):
    # 300mm cube exceeds the 256 build volume — must still return 200 + a flag.
    _mock(monkeypatch, dims=(300.0, 300.0, 300.0), supports=False)
    resp = client.post("/slice", files={"file": _STL}, data=_FORM)
    assert resp.status_code == 200
    assert resp.json()["fits_build_volume"] is False


def test_requires_supports_true(monkeypatch):
    _mock(monkeypatch, dims=(50.0, 50.0, 50.0), supports=True)
    body = client.post("/slice", files={"file": _STL}, data=_FORM).json()
    assert body["requires_supports"] is True


def test_check_supports_disabled_returns_null(monkeypatch):
    _mock(monkeypatch, dims=(50.0, 50.0, 50.0), supports=True)
    data = {**_FORM, "check_supports": "false"}
    body = client.post("/slice", files={"file": _STL}, data=data).json()
    assert body["requires_supports"] is None


def test_build_volume_override(monkeypatch):
    # A 150mm model fits 256³ but not a custom 120³ volume.
    _mock(monkeypatch, dims=(150.0, 150.0, 100.0), supports=False)
    data = {**_FORM, "build_volume_x": "120", "build_volume_y": "120", "build_volume_z": "120"}
    body = client.post("/slice", files={"file": _STL}, data=data).json()
    assert body["build_volume_mm"] == {"x": 120.0, "y": 120.0, "z": 120.0}
    assert body["fits_build_volume"] is False
