from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
import subprocess
import os
import re
import uuid
from pathlib import Path

app = FastAPI(
    title="SuperSlice API",
    description="3D Print Estimation Service using PrusaSlicer",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directories
UPLOAD_DIR = Path("/app/uploads")
OUTPUT_DIR = Path("/app/output")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Filament densities (g/cm³)
FILAMENT_DENSITIES = {
    "PLA": 1.24,
    "PETG": 1.27,
    "ABS": 1.04,
    "TPU": 1.21,
    "NYLON": 1.14,
    "ASA": 1.07,
}


class SliceRequest(BaseModel):
    """Request model for slicing parameters"""
    layer_height: float = Field(default=0.2, ge=0.1, le=0.4, description="Layer height in mm")
    infill_density: int = Field(default=15, ge=0, le=100, description="Infill percentage")
    wall_count: int = Field(default=2, ge=1, le=10, description="Number of perimeter walls")
    filament_type: str = Field(default="PLA", description="Filament type")
    filament_density: Optional[float] = Field(default=None, description="Custom filament density (g/cm³)")


class SliceResponse(BaseModel):
    """Response model with slicing results"""
    success: bool
    print_time_minutes: float
    print_time_formatted: str
    filament_length_mm: float
    filament_volume_cm3: float
    filament_weight_g: float
    filament_type: str
    layer_height: float
    infill_density: int
    wall_count: int


def parse_gcode_statistics(gcode_path: str, filament_density: float) -> dict:
    """
    Parse G-code file to extract print statistics
    
    Args:
        gcode_path: Path to the G-code file
        filament_density: Filament density in g/cm³
        
    Returns:
        Dictionary with print statistics
    """
    stats = {
        "filament_length_mm": 0.0,
        "filament_volume_cm3": 0.0,
        "print_time_seconds": 0,
        "print_time_formatted": "0m 0s"
    }
    
    with open(gcode_path, 'r') as f:
        for line in f:
            # Extract filament length
            if "; filament used [mm]" in line:
                match = re.search(r'=\s*([\d.]+)', line)
                if match:
                    stats["filament_length_mm"] = float(match.group(1))
            
            # Extract filament volume
            elif "; filament used [cm3]" in line:
                match = re.search(r'=\s*([\d.]+)', line)
                if match:
                    stats["filament_volume_cm3"] = float(match.group(1))
            
            # Extract print time
            elif "; estimated printing time (normal mode)" in line:
                match = re.search(r'=\s*(.+)', line)
                if match:
                    time_str = match.group(1).strip()
                    stats["print_time_formatted"] = time_str
                    
                    # Convert to seconds
                    hours = minutes = seconds = 0
                    if 'h' in time_str:
                        hours = int(re.search(r'(\d+)h', time_str).group(1))
                    if 'm' in time_str:
                        minutes = int(re.search(r'(\d+)m', time_str).group(1))
                    if 's' in time_str:
                        seconds = int(re.search(r'(\d+)s', time_str).group(1))
                    
                    stats["print_time_seconds"] = hours * 3600 + minutes * 60 + seconds
    
    # Calculate weight from volume and density
    stats["filament_weight_g"] = stats["filament_volume_cm3"] * filament_density
    
    return stats


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "SuperSlice API",
        "status": "running",
        "version": "1.0.0"
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
        file: 3D model file (STL or 3MF) - REQUIRED
        layer_height: Layer height in mm - REQUIRED
        infill_density: Infill percentage (0 - 100) - REQUIRED
        wall_count: Number of perimeter walls (1 - 20) - REQUIRED
        filament_type: Filament type (defaults to PLA if not provided)
        filament_density: Custom filament density in g/cm³ (overrides filament_type)
        
    Returns:
        SliceResponse with print statistics
    """
    # Validate file extension
    if not file.filename or not file.filename.lower().endswith(('.stl', '.3mf')):
        raise HTTPException(status_code=400, detail="Only STL and 3MF files are supported")
    
    # Validate required parameters
    if layer_height is None:
        raise HTTPException(status_code=400, detail="layer_height is required")
    
    if infill_density is None:
        raise HTTPException(status_code=400, detail="infill_density is required")
    
    if wall_count is None:
        raise HTTPException(status_code=400, detail="wall_count is required")
    
    # Validate parameter ranges
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
    
    # Determine filament density
    if filament_density is None:
        filament_density = FILAMENT_DENSITIES.get(filament_type.upper(), 1.24)
    
    # Generate unique ID for this job
    job_id = str(uuid.uuid4())
    
    # Save uploaded file
    input_path = UPLOAD_DIR / f"{job_id}_{file.filename}"
    output_path = OUTPUT_DIR / f"{job_id}.gcode"
    
    try:
        # Save uploaded file
        with open(input_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Build PrusaSlicer command
        cmd = [
            "/slic3r/squashfs-root/usr/bin/prusa-slicer",
            "--layer-height", str(layer_height),
            "--perimeters", str(wall_count),
            "--fill-density", f"{infill_density}%",
            "--export-gcode",
            "--output", str(output_path),
            str(input_path)
        ]
        
        # Run PrusaSlicer
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout
        )
        
        if result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"Slicing failed: {result.stderr}"
            )
        
        # Parse G-code statistics
        stats = parse_gcode_statistics(str(output_path), filament_density)
        
        # Clean up files
        input_path.unlink()
        output_path.unlink()
        
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
            wall_count=wall_count
        )
        
    except subprocess.TimeoutExpired:
        # Clean up on timeout
        if input_path.exists():
            input_path.unlink()
        if output_path.exists():
            output_path.unlink()
        raise HTTPException(status_code=408, detail="Slicing timeout - model too complex")
    
    except Exception as e:
        # Clean up on error
        if input_path.exists():
            input_path.unlink()
        if output_path.exists():
            output_path.unlink()
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
