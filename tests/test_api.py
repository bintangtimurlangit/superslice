"""API-level tests using FastAPI's TestClient.

Slicing itself (the PrusaSlicer subprocess) is mocked so these run without the
binary; they exercise routing, validation, and response shaping.
"""
import io

import pytest
from fastapi.testclient import TestClient

from app import routes
from app.main import app

client = TestClient(app)


def test_root_health():
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "running"


def test_filament_types():
    resp = client.get("/filament-types")
    assert resp.status_code == 200
    assert "PLA" in resp.json()["filament_types"]


def test_rejects_unsupported_extension():
    resp = client.post(
        "/slice",
        files={"file": ("model.txt", b"not a model", "text/plain")},
        data={"layer_height": "0.2", "infill_density": "20", "wall_count": "3"},
    )
    assert resp.status_code == 400


def test_rejects_empty_file():
    resp = client.post(
        "/slice",
        files={"file": ("model.stl", b"", "application/octet-stream")},
        data={"layer_height": "0.2", "infill_density": "20", "wall_count": "3"},
    )
    assert resp.status_code == 400
    assert "empty" in resp.json()["detail"].lower()


@pytest.mark.parametrize(
    "field, value",
    [("layer_height", "5"), ("infill_density", "200"), ("wall_count", "0")],
)
def test_rejects_out_of_range_parameters(field, value):
    data = {"layer_height": "0.2", "infill_density": "20", "wall_count": "3"}
    data[field] = value
    resp = client.post(
        "/slice",
        files={"file": ("cube.stl", b"solid x\nendsolid x\n", "application/octet-stream")},
        data=data,
    )
    assert resp.status_code == 400


def test_successful_slice_is_shaped_correctly(monkeypatch):
    # Pretend PrusaSlicer ran successfully...
    monkeypatch.setattr(routes, "run_slicer", lambda *a, **k: None)
    # ...and produced these stats.
    monkeypatch.setattr(
        routes,
        "parse_gcode_statistics",
        lambda path, density: {
            "filament_length_mm": 1506.53,
            "filament_volume_cm3": 3.62,
            "filament_weight_g": 3.62 * density,
            "print_time_seconds": 1162,
            "print_time_formatted": "19m 22s",
        },
    )

    resp = client.post(
        "/slice",
        files={"file": ("cube.stl", b"solid x\nendsolid x\n", "application/octet-stream")},
        data={
            "layer_height": "0.2",
            "infill_density": "20",
            "wall_count": "3",
            "filament_type": "PETG",
        },
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["print_time_formatted"] == "19m 22s"
    assert body["filament_length_mm"] == 1506.53
    # weight uses PETG density (1.27)
    assert body["filament_weight_g"] == pytest.approx(3.62 * 1.27, abs=0.01)
