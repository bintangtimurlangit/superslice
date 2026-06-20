"""HTTP routes for the SuperSlice API."""
import subprocess
import uuid
from pathlib import Path
from typing import Optional, Tuple

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile

from ..config import (
    API_TITLE,
    API_VERSION,
    FILAMENT_DENSITIES,
    HISTORY_ENABLED,
    OUTPUT_DIR,
    SLICER_NAME,
    SLICER_VERSION,
    UPLOAD_DIR,
)
from ..core.errors import APIError
from ..core.security import enforce_rate_limit, require_api_key
from ..models import (
    ErrorResponse,
    HistoryItem,
    HistoryList,
    JobCreated,
    JobStatusResponse,
    SliceResponse,
    VersionInfo,
)
from ..services import history
from ..services.jobs import job_manager
from ..services.slicing import (
    SliceParams,
    check_disk_space,
    cleanup_files,
    perform_slice,
    save_upload,
    validate_filename,
    validate_params,
)

router = APIRouter()

# Dependencies that guard the slice endpoints (no-ops unless configured).
_SLICE_GUARDS = [Depends(require_api_key), Depends(enforce_rate_limit)]

_ERROR_RESPONSES = {
    400: {"model": ErrorResponse},
    408: {"model": ErrorResponse},
    413: {"model": ErrorResponse},
    500: {"model": ErrorResponse},
}


@router.get("/", tags=["health"])
async def root():
    """Service info / health endpoint."""
    return {"service": API_TITLE, "status": "running", "version": API_VERSION}


@router.get("/healthz", tags=["health"])
async def healthz():
    """Liveness probe — cheap and dependency-free."""
    return {"status": "ok"}


@router.get("/version", response_model=VersionInfo, tags=["health"])
async def version():
    """Service and bundled-slicer versions."""
    return VersionInfo(
        service=API_TITLE,
        version=API_VERSION,
        slicer=f"{SLICER_NAME} {SLICER_VERSION}",
    )


@router.get("/filament-types", tags=["slicing"])
async def get_filament_types():
    """Return available filament types and their densities."""
    return {"filament_types": FILAMENT_DENSITIES}


@router.post(
    "/slice",
    response_model=SliceResponse,
    responses=_ERROR_RESPONSES,
    dependencies=_SLICE_GUARDS,
    tags=["slicing"],
)
async def slice_model(
    file: UploadFile = File(...),
    layer_height: float = Form(..., description="Layer height in mm (0.01-1.0)"),
    infill_density: int = Form(..., description="Infill percentage (0-100)"),
    wall_count: int = Form(..., description="Number of perimeter walls (1-20)"),
    filament_type: str = Form("PLA"),
    filament_density: Optional[float] = Form(None),
):
    """Slice a model synchronously and return print statistics."""
    input_path, output_path, params, filename = await _prepare_slice(
        file, layer_height, infill_density, wall_count, filament_type, filament_density
    )
    try:
        return await _run_slice(input_path, output_path, params, filename)
    finally:
        cleanup_files(input_path, output_path)


@router.post(
    "/jobs",
    response_model=JobCreated,
    status_code=202,
    dependencies=_SLICE_GUARDS,
    tags=["slicing"],
)
async def create_slice_job(
    file: UploadFile = File(...),
    layer_height: float = Form(...),
    infill_density: int = Form(...),
    wall_count: int = Form(...),
    filament_type: str = Form("PLA"),
    filament_density: Optional[float] = Form(None),
):
    """Accept a slice for async processing; poll `GET /jobs/{job_id}` for the result.

    Useful for large/complex models that would exceed a normal request timeout.
    """
    input_path, output_path, params, filename = await _prepare_slice(
        file, layer_height, infill_density, wall_count, filament_type, filament_density
    )

    async def runner() -> SliceResponse:
        try:
            return await _run_slice(input_path, output_path, params, filename)
        finally:
            cleanup_files(input_path, output_path)

    job = await job_manager.submit(runner)
    return JobCreated(job_id=job.id, status=job.status, status_url=f"/jobs/{job.id}")


@router.get(
    "/jobs/{job_id}",
    response_model=JobStatusResponse,
    responses={404: {"model": ErrorResponse}},
    tags=["slicing"],
)
async def get_slice_job(job_id: str):
    """Return the status (and result, once finished) of an async slice job."""
    job = await job_manager.get(job_id)
    if job is None:
        raise APIError(404, "JOB_NOT_FOUND", "Job not found")
    return job.to_status()


@router.get("/history", response_model=HistoryList, tags=["history"])
async def list_history(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """List past slices (opt-in; requires HISTORY_ENABLED)."""
    _require_history()
    return HistoryList(count=history.count(), items=history.list_records(limit, offset))


@router.get(
    "/history/{record_id}",
    response_model=HistoryItem,
    responses={404: {"model": ErrorResponse}},
    tags=["history"],
)
async def get_history_record(record_id: int):
    """Fetch a single history record (opt-in; requires HISTORY_ENABLED)."""
    _require_history()
    record = history.get_record(record_id)
    if record is None:
        raise APIError(404, "RECORD_NOT_FOUND", "History record not found")
    return record


# --- helpers --------------------------------------------------------------

async def _prepare_slice(
    file: UploadFile,
    layer_height: float,
    infill_density: int,
    wall_count: int,
    filament_type: str,
    filament_density: Optional[float],
) -> Tuple[Path, Path, SliceParams, Optional[str]]:
    """Validate inputs, guard resources, and save the upload to disk."""
    validate_filename(file.filename)
    params = SliceParams(
        layer_height=layer_height,
        infill_density=infill_density,
        wall_count=wall_count,
        filament_type=filament_type,
        filament_density=filament_density,
    )
    validate_params(params)
    check_disk_space()

    job_id = str(uuid.uuid4())
    input_path = UPLOAD_DIR / f"{job_id}_{file.filename}"
    output_path = OUTPUT_DIR / f"{job_id}.gcode"
    await save_upload(file, input_path)
    return input_path, output_path, params, file.filename


async def _run_slice(input_path, output_path, params, filename) -> SliceResponse:
    """Run a slice, mapping slicer subprocess failures to API errors."""
    try:
        return await perform_slice(input_path, output_path, params, filename)
    except subprocess.TimeoutExpired:
        raise APIError(408, "SLICE_TIMEOUT", "Slicing timeout - model too complex")
    except subprocess.CalledProcessError as e:
        raise APIError(500, "SLICE_FAILED", f"Slicing failed: {e.stderr}")


def _require_history() -> None:
    if not HISTORY_ENABLED:
        raise APIError(404, "HISTORY_DISABLED", "Slicing history is not enabled")
