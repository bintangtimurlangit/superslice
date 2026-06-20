"""Tests for the auxiliary endpoints, structured errors, and resource guards."""
from fastapi.testclient import TestClient

from app.config import API_VERSION, OUTPUT_DIR, UPLOAD_DIR
from app.main import app
from app.services import slicing

client = TestClient(app)

_VALID_STL = ("cube.stl", b"solid x\nendsolid x\n", "application/octet-stream")
_VALID_FORM = {"layer_height": "0.2", "infill_density": "20", "wall_count": "3"}


def test_healthz():
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_version():
    body = client.get("/version").json()
    assert body["version"] == API_VERSION
    assert "PrusaSlicer" in body["slicer"]


def test_structured_error_envelope():
    resp = client.post(
        "/slice",
        files={"file": ("model.txt", b"x", "text/plain")},
        data=_VALID_FORM,
    )
    assert resp.status_code == 400
    body = resp.json()
    assert body["error"]["code"] == "UNSUPPORTED_FILE"
    assert body["detail"]  # human-readable message preserved


def test_history_disabled_by_default():
    resp = client.get("/history")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "HISTORY_DISABLED"


def test_disk_guard_blocks_when_low(monkeypatch):
    # Demand an absurd amount of free space so the guard always trips.
    monkeypatch.setattr(slicing, "MIN_FREE_DISK_MB", 10**12)
    resp = client.post("/slice", files={"file": _VALID_STL}, data=_VALID_FORM)
    assert resp.status_code == 503
    assert resp.json()["error"]["code"] == "INSUFFICIENT_STORAGE"


def test_sweep_removes_orphaned_files():
    (UPLOAD_DIR / "orphan_input.stl").write_text("x")
    (OUTPUT_DIR / "orphan_output.gcode").write_text("y")
    removed = slicing.sweep_work_dirs()
    assert removed >= 2
    assert not (UPLOAD_DIR / "orphan_input.stl").exists()
