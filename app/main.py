"""SuperSlice API - 3D Print Estimation Service"""
import uuid
import subprocess
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from config import (
    API_TITLE,
    API_DESCRIPTION,
    API_VERSION,
    CORS_ORIGINS,
    UPLOAD_DIR,
    OUTPUT_DIR,
    FILAMENT_DENSITIES,
)
from models import SliceResponse
from slicer import parse_gcode_statistics, run_slicer


app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": API_TITLE,
        "status": "running",
        "version": API_VERSION
    }


@app.get("/filament-types")
async def get_filament_types():
    """Get available filament types and their densities"""
    return {
        "filament_types": FILAMENT_DENSITIES
    }


@app.post("/slice", response_model=SliceResponse)
async def slice_model(
    file: UploadFile = File(...),
    layer_height: float = Form(...),
    infill_density: int = Form(...),
    wall_count: int = Form(...),
    filament_type: str = Form("PLA"),
    filament_density: Optional[float] = Form(None)
):
    """
    Slice a 3D model and return print statistics
    
    Args:
        file: 3D model file (STL or 3MF)
        layer_height: Layer height in mm (0.01 - 1.0)
        infill_density: Infill percentage (0 - 100)
        wall_count: Number of perimeter walls (1 - 20)
        filament_type: Filament type (defaults to PLA)
        filament_density: Custom filament density in g/cm³ (overrides filament_type)
        
    Returns:
        SliceResponse with print statistics
    """
    # Validate file extension
    if not file.filename or not file.filename.lower().endswith(('.stl', '.3mf')):
        raise HTTPException(
            status_code=400, 
            detail="Only STL and 3MF files are supported"
        )
    
    # Validate parameter ranges
    _validate_parameters(layer_height, infill_density, wall_count)
    
    # Determine filament density
    if filament_density is None:
        filament_density = FILAMENT_DENSITIES.get(filament_type.upper(), 1.24)
    
    # Generate unique ID for this job
    job_id = str(uuid.uuid4())
    
    # Define file paths
    input_path = UPLOAD_DIR / f"{job_id}_{file.filename}"
    output_path = OUTPUT_DIR / f"{job_id}.gcode"
    
    try:
        # Save uploaded file
        await _save_upload(file, input_path)
        
        # Run PrusaSlicer
        run_slicer(input_path, output_path, layer_height, wall_count, infill_density)
        
        # Parse G-code statistics
        stats = parse_gcode_statistics(str(output_path), filament_density)
        
        # Build response
        response = SliceResponse(
            success=True,
            print_time_minutes=round(stats["print_time_seconds"] / 60, 2),
            print_time_formatted=stats["print_time_formatted"],
            filament_length_mm=round(stats["filament_length_mm"], 2),
            filament_volume_cm3=round(stats["filament_volume_cm3"], 2),
            filament_weight_g=round(stats["filament_weight_g"], 2),
            filament_type=filament_type,
            layer_height=layer_height,
            infill_density=infill_density,
            wall_count=wall_count
        )
        
        return response
        
    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=408, 
            detail="Slicing timeout - model too complex"
        )
    
    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Slicing failed: {e.stderr}"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # Clean up files
        _cleanup_files(input_path, output_path)


def _validate_parameters(layer_height: float, infill_density: int, wall_count: int):
    """Validate slicing parameters"""
    if layer_height < 0.01 or layer_height > 1.0:
        raise HTTPException(
            status_code=400,
            detail=f"layer_height must be between 0.01 and 1.0 mm, got {layer_height}"
        )
    
    if infill_density < 0 or infill_density > 100:
        raise HTTPException(
            status_code=400,
            detail=f"infill_density must be between 0 and 100, got {infill_density}"
        )
    
    if wall_count < 1 or wall_count > 20:
        raise HTTPException(
            status_code=400,
            detail=f"wall_count must be between 1 and 20, got {wall_count}"
        )


async def _save_upload(file: UploadFile, path: Path):
    """Save uploaded file to disk"""
    with open(path, "wb") as f:
        content = await file.read()
        f.write(content)


def _cleanup_files(*paths: Path):
    """Remove temporary files"""
    for path in paths:
        if path.exists():
            path.unlink()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
