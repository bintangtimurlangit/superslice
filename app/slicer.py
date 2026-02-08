"""PrusaSlicer integration and G-code parsing"""
import re
import subprocess
from pathlib import Path
from typing import Dict

from config import PRUSASLICER_PATH, SLICE_TIMEOUT


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
    Convert time string (e.g., '1h 30m 45s') to total seconds
    
    Args:
        time_str: Time string from G-code
        
    Returns:
        Total seconds as integer
    """
    hours = minutes = seconds = 0
    
    if 'h' in time_str:
        hours = int(re.search(r'(\d+)h', time_str).group(1))
    if 'm' in time_str:
        minutes = int(re.search(r'(\d+)m', time_str).group(1))
    if 's' in time_str:
        seconds = int(re.search(r'(\d+)s', time_str).group(1))
    
    return hours * 3600 + minutes * 60 + seconds


def run_slicer(
    input_path: Path,
    output_path: Path,
    layer_height: float,
    wall_count: int,
    infill_density: int
) -> subprocess.CompletedProcess:
    """
    Execute PrusaSlicer with specified parameters
    
    Args:
        input_path: Path to input 3D model file
        output_path: Path for output G-code file
        layer_height: Layer height in mm
        wall_count: Number of perimeter walls
        infill_density: Infill percentage
        
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
        "--export-gcode",
        "--output", str(output_path),
        str(input_path)
    ]
    
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
