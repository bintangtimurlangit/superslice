"""Configuration settings for SuperSlice API"""
import os
from pathlib import Path

# Directories
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "/app/uploads"))
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "/app/output"))

# Ensure directories exist
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# PrusaSlicer configuration
PRUSASLICER_PATH = os.getenv(
    "PRUSASLICER_PATH", 
    "/slic3r/squashfs-root/usr/bin/prusa-slicer"
)

# Processing limits
SLICE_TIMEOUT = int(os.getenv("SLICE_TIMEOUT", "120"))  # seconds
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "104857600"))  # 100MB in bytes

# Filament densities (g/cm³)
FILAMENT_DENSITIES = {
    "PLA": 1.24,
    "PETG": 1.27,
    "ABS": 1.04,
    "TPU": 1.21,
    "NYLON": 1.14,
    "ASA": 1.07,
}

# API metadata
API_TITLE = "SuperSlice API"
API_DESCRIPTION = "3D Print Estimation Service using PrusaSlicer"
API_VERSION = "1.0.0"

# CORS settings
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
