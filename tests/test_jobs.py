"""Tests for the async job manager and job endpoints."""
import asyncio

from fastapi.testclient import TestClient

from app.core.errors import APIError
from app.main import app
from app.services import slicing
from app.services.jobs import JobManager

client = TestClient(app)

_VALID_STL = ("cube.stl", b"solid x\nendsolid x\n", "application/octet-stream")
_VALID_FORM = {"layer_height": "0.2", "infill_density": "20", "wall_count": "3"}


async def _wait(manager, job_id):
    for _ in range(200):
        job = await manager.get(job_id)
        if job.status in ("succeeded", "failed"):
            return job
        await asyncio.sleep(0.01)
    raise AssertionError("job did not finish")


def test_job_manager_stores_success():
    async def go():
        manager = JobManager()

        async def runner():
            return "RESULT"

        job = await manager.submit(runner)
        return await _wait(manager, job.id)

    job = asyncio.run(go())
    assert job.status == "succeeded"
    assert job.result == "RESULT"


def test_job_manager_captures_api_error():
    async def go():
        manager = JobManager()

        async def runner():
            raise APIError(500, "BOOM", "it failed")

        job = await manager.submit(runner)
        return await _wait(manager, job.id)

    job = asyncio.run(go())
    assert job.status == "failed"
    assert job.error_code == "BOOM"


def test_job_manager_prunes_to_retention():
    async def go():
        manager = JobManager(retention=3)

        async def runner():
            return "x"

        ids = []
        for _ in range(6):
            job = await manager.submit(runner)
            await _wait(manager, job.id)
            ids.append(job.id)
        # Only the most recent few are retained.
        present = [bool(await manager.get(i)) for i in ids]
        return present

    present = asyncio.run(go())
    assert sum(present) <= 3
    assert present[-1] is True  # newest kept


def test_create_job_returns_202(monkeypatch):
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
    resp = client.post("/jobs", files={"file": _VALID_STL}, data=_VALID_FORM)
    assert resp.status_code == 202
    body = resp.json()
    assert body["job_id"]
    assert body["status_url"].endswith(body["job_id"])


def test_get_unknown_job_404():
    resp = client.get("/jobs/does-not-exist")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "JOB_NOT_FOUND"
