"""Slicing orchestration shared by the sync and async endpoints."""
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from fastapi import UploadFile
from fastapi.concurrency import run_in_threadpool

from . import history
from ..config import (
    FILAMENT_DENSITIES,
    MAX_FILE_SIZE,
    MIN_FREE_DISK_MB,
    OUTPUT_DIR,
    UPLOAD_DIR,
)
from ..core.errors import APIError
from ..core.security import slice_slot
from ..models import SliceResponse
from .slicer import parse_gcode_statistics, run_slicer

DEFAULT_FILAMENT_DENSITY = 1.24  # PLA, used when a type is unknown


@dataclass
class SliceParams:
    layer_height: float
    infill_density: int
    wall_count: int
    filament_type: str = "PLA"
    filament_density: Optional[float] = None


def validate_params(params: SliceParams) -> None:
    """Range-check slicing parameters, raising a 400 APIError on any failure."""
    if params.layer_height < 0.01 or params.layer_height > 1.0:
        raise APIError(
            400, "INVALID_PARAMETER",
            f"layer_height must be between 0.01 and 1.0 mm, got {params.layer_height}",
        )
    if params.infill_density < 0 or params.infill_density > 100:
        raise APIError(
            400, "INVALID_PARAMETER",
            f"infill_density must be between 0 and 100, got {params.infill_density}",
        )
    if params.wall_count < 1 or params.wall_count > 20:
        raise APIError(
            400, "INVALID_PARAMETER",
            f"wall_count must be between 1 and 20, got {params.wall_count}",
        )


def validate_filename(filename: Optional[str]) -> None:
    if not filename or not filename.lower().endswith((".stl", ".3mf")):
        raise APIError(400, "UNSUPPORTED_FILE", "Only STL and 3MF files are supported")


def resolve_density(params: SliceParams) -> float:
    if params.filament_density is not None:
        return params.filament_density
    return FILAMENT_DENSITIES.get(params.filament_type.upper(), DEFAULT_FILAMENT_DENSITY)


def check_disk_space() -> None:
    """Refuse work when free disk is below MIN_FREE_DISK_MB (if configured)."""
    if MIN_FREE_DISK_MB <= 0:
        return
    free_mb = shutil.disk_usage(UPLOAD_DIR).free / (1024 * 1024)
    if free_mb < MIN_FREE_DISK_MB:
        raise APIError(503, "INSUFFICIENT_STORAGE", "Insufficient disk space to process slice")


async def save_upload(file: UploadFile, path: Path) -> None:
    """Stream an uploaded file to disk, enforcing the configured size limit."""
    bytes_written = 0
    with open(path, "wb") as f:
        while chunk := await file.read(1024 * 1024):
            bytes_written += len(chunk)
            if bytes_written > MAX_FILE_SIZE:
                f.close()
                path.unlink(missing_ok=True)
                raise APIError(
                    413, "FILE_TOO_LARGE",
                    f"File exceeds maximum size of {MAX_FILE_SIZE} bytes",
                )
            f.write(chunk)
    if bytes_written == 0:
        path.unlink(missing_ok=True)
        raise APIError(400, "EMPTY_FILE", "Uploaded file is empty")


def cleanup_files(*paths: Path) -> None:
    for path in paths:
        if path.exists():
            path.unlink()


async def perform_slice(
    input_path: Path,
    output_path: Path,
    params: SliceParams,
    filename: Optional[str] = None,
) -> SliceResponse:
    """Run the slicer (bounded by the concurrency cap), parse, and record it."""
    density = resolve_density(params)

    async with slice_slot():
        await run_in_threadpool(
            run_slicer,
            input_path, output_path,
            params.layer_height, params.wall_count, params.infill_density,
        )

    stats = parse_gcode_statistics(str(output_path), density)
    response = SliceResponse(
        success=True,
        print_time_minutes=round(stats["print_time_seconds"] / 60, 2),
        print_time_formatted=stats["print_time_formatted"],
        filament_length_mm=round(stats["filament_length_mm"], 2),
        filament_volume_cm3=round(stats["filament_volume_cm3"], 2),
        filament_weight_g=round(stats["filament_weight_g"], 2),
        filament_type=params.filament_type,
        layer_height=params.layer_height,
        infill_density=params.infill_density,
        wall_count=params.wall_count,
    )
    history.record(params, response, filename)
    return response


def sweep_work_dirs() -> int:
    """Delete any files left in the work directories (orphans from crashes)."""
    removed = 0
    for directory in (UPLOAD_DIR, OUTPUT_DIR):
        if not directory.exists():
            continue
        for entry in directory.iterdir():
            if entry.is_file():
                entry.unlink(missing_ok=True)
                removed += 1
    return removed
