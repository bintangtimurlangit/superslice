"""PrusaSlicer integration and G-code parsing"""
import re
import subprocess
from pathlib import Path
from typing import Dict, Optional, Tuple

from ..config import PRUSASLICER_PATH, SLICE_TIMEOUT


def parse_gcode_statistics(gcode_path: str, filament_density: float) -> Dict[str, any]:
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
                    stats["print_time_seconds"] = _parse_time_string(time_str)
    
    # Calculate weight from volume and density
    stats["filament_weight_g"] = stats["filament_volume_cm3"] * filament_density
    
    return stats


def _parse_time_string(time_str: str) -> int:
    """
    Convert time string (e.g., '1d 2h 30m 45s') to total seconds

    Tolerates any missing units (e.g. '19m 22s' or '45s') without raising.

    Args:
        time_str: Time string from G-code

    Returns:
        Total seconds as integer
    """
    units = {'d': 86400, 'h': 3600, 'm': 60, 's': 1}
    total = 0
    for value, unit in re.findall(r'(\d+)\s*([dhms])', time_str):
        total += int(value) * units[unit]
    return total


def run_slicer(
    input_path: Path,
    output_path: Path,
    layer_height: float,
    wall_count: int,
    infill_density: int,
    bed: Optional[Tuple[float, float]] = None,
    max_height: Optional[float] = None,
    with_supports: bool = False,
) -> subprocess.CompletedProcess:
    """
    Execute PrusaSlicer with specified parameters.

    Args:
        input_path: Path to input 3D model file
        output_path: Path for output G-code file
        layer_height: Layer height in mm
        wall_count: Number of perimeter walls
        infill_density: Infill percentage
        bed: Optional (width, depth) of the slicing bed in mm. When given, the
            object is centered so its original position never matters.
        max_height: Optional max print height in mm.
        with_supports: Enable automatic support material (used for detection).

    Returns:
        CompletedProcess result from subprocess

    Raises:
        subprocess.TimeoutExpired: If slicing exceeds timeout
        subprocess.CalledProcessError: If slicing fails
    """
    cmd = [
        PRUSASLICER_PATH,
        "--layer-height", str(layer_height),
        "--perimeters", str(wall_count),
        "--fill-density", f"{infill_density}%",
    ]

    if bed is not None:
        width, depth = bed
        cmd += [
            "--bed-shape", f"0x0,{width}x0,{width}x{depth},0x{depth}",
            "--center", f"{width / 2},{depth / 2}",
        ]
    if max_height is not None:
        cmd += ["--max-print-height", str(max_height)]
    if with_supports:
        cmd += ["--support-material"]

    cmd += ["--export-gcode", "--output", str(output_path), str(input_path)]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=SLICE_TIMEOUT
    )

    if result.returncode != 0:
        raise subprocess.CalledProcessError(
            result.returncode,
            cmd,
            result.stdout,
            result.stderr
        )

    return result


def get_model_dimensions(input_path: Path) -> Tuple[float, float, float]:
    """
    Return the model's bounding-box size (x, y, z) in mm via PrusaSlicer --info.

    Falls back to (0, 0, 0) if the size cannot be determined, so a failure here
    never blocks an estimate.
    """
    result = subprocess.run(
        [PRUSASLICER_PATH, "--info", str(input_path)],
        capture_output=True,
        text=True,
        timeout=SLICE_TIMEOUT,
    )
    dims = []
    for axis in ("x", "y", "z"):
        match = re.search(rf"size_{axis}\s*=\s*([\d.]+)", result.stdout)
        dims.append(float(match.group(1)) if match else 0.0)
    return dims[0], dims[1], dims[2]


def gcode_has_support_material(gcode_path: str) -> bool:
    """True if the G-code contains support-material extrusions."""
    with open(gcode_path) as f:
        for line in f:
            if line.startswith(";TYPE:Support material"):
                return True
    return False
