"""HTTP routes for the SuperSlice API."""
import subprocess
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool

from .config import (
    API_TITLE,
    API_VERSION,
    FILAMENT_DENSITIES,
    MAX_FILE_SIZE,
    OUTPUT_DIR,
    UPLOAD_DIR,
)
from .models import SliceResponse
from .slicer import parse_gcode_statistics, run_slicer

router = APIRouter()

DEFAULT_FILAMENT_DENSITY = 1.24  # PLA, used when a type is unknown


@router.get("/")
async def root():
    """Health check endpoint."""
    return {"service": API_TITLE, "status": "running", "version": API_VERSION}


@router.get("/filament-types")
async def get_filament_types():
    """Return available filament types and their densities."""
    return {"filament_types": FILAMENT_DENSITIES}


@router.post("/slice", response_model=SliceResponse)
async def slice_model(
    file: UploadFile = File(...),
    layer_height: float = Form(...),
    infill_density: int = Form(...),
    wall_count: int = Form(...),
    filament_type: str = Form("PLA"),
    filament_density: Optional[float] = Form(None),
):
    """
    Slice a 3D model and return print statistics.

    Args:
        file: 3D model file (STL or 3MF)
        layer_height: Layer height in mm (0.01 - 1.0)
        infill_density: Infill percentage (0 - 100)
        wall_count: Number of perimeter walls (1 - 20)
        filament_type: Filament type (defaults to PLA)
        filament_density: Custom density in g/cm³ (overrides filament_type)

    Returns:
        SliceResponse with print statistics.
    """
    if not file.filename or not file.filename.lower().endswith((".stl", ".3mf")):
        raise HTTPException(
            status_code=400, detail="Only STL and 3MF files are supported"
        )

    _validate_parameters(layer_height, infill_density, wall_count)

    if filament_density is None:
        filament_density = FILAMENT_DENSITIES.get(
            filament_type.upper(), DEFAULT_FILAMENT_DENSITY
        )

    job_id = str(uuid.uuid4())
    input_path = UPLOAD_DIR / f"{job_id}_{file.filename}"
    output_path = OUTPUT_DIR / f"{job_id}.gcode"

    try:
        await _save_upload(file, input_path)

        # Run PrusaSlicer (blocking subprocess) without stalling the event loop.
        await run_in_threadpool(
            run_slicer,
            input_path, output_path, layer_height, wall_count, infill_density,
        )

        stats = parse_gcode_statistics(str(output_path), filament_density)

        return SliceResponse(
            success=True,
            print_time_minutes=round(stats["print_time_seconds"] / 60, 2),
            print_time_formatted=stats["print_time_formatted"],
            filament_length_mm=round(stats["filament_length_mm"], 2),
            filament_volume_cm3=round(stats["filament_volume_cm3"], 2),
            filament_weight_g=round(stats["filament_weight_g"], 2),
            filament_type=filament_type,
            layer_height=layer_height,
            infill_density=infill_density,
            wall_count=wall_count,
        )

    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=408, detail="Slicing timeout - model too complex"
        )

    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Slicing failed: {e.stderr}")

    except HTTPException:
        # Validation errors (e.g. empty/oversized upload) already carry the
        # right status code — don't let the generic handler below mask them.
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        _cleanup_files(input_path, output_path)


def _validate_parameters(layer_height: float, infill_density: int, wall_count: int):
    """Validate slicing parameters, raising HTTP 400 on any out-of-range value."""
    if layer_height < 0.01 or layer_height > 1.0:
        raise HTTPException(
            status_code=400,
            detail=f"layer_height must be between 0.01 and 1.0 mm, got {layer_height}",
        )

    if infill_density < 0 or infill_density > 100:
        raise HTTPException(
            status_code=400,
            detail=f"infill_density must be between 0 and 100, got {infill_density}",
        )

    if wall_count < 1 or wall_count > 20:
        raise HTTPException(
            status_code=400,
            detail=f"wall_count must be between 1 and 20, got {wall_count}",
        )


async def _save_upload(file: UploadFile, path: Path):
    """Stream an uploaded file to disk, enforcing the configured size limit."""
    bytes_written = 0
    with open(path, "wb") as f:
        while chunk := await file.read(1024 * 1024):
            bytes_written += len(chunk)
            if bytes_written > MAX_FILE_SIZE:
                f.close()
                path.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=413,
                    detail=f"File exceeds maximum size of {MAX_FILE_SIZE} bytes",
                )
            f.write(chunk)

    if bytes_written == 0:
        path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="Uploaded file is empty")


def _cleanup_files(*paths: Path):
    """Remove temporary files."""
    for path in paths:
        if path.exists():
            path.unlink()
