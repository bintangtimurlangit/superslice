"""Configuration settings for SuperSlice API"""
import os
from pathlib import Path

# Directories
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "/app/uploads"))
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "/app/output"))

# Ensure directories exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# PrusaSlicer configuration
PRUSASLICER_PATH = os.getenv(
    "PRUSASLICER_PATH",
    "/opt/prusaslicer/usr/bin/prusa-slicer"
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

# Slicer metadata (the bundled PrusaSlicer build; see docs/SLICER.md)
SLICER_NAME = "PrusaSlicer"
SLICER_VERSION = "2.8.1"

# API metadata
API_TITLE = "SuperSlice API"
API_DESCRIPTION = "3D Print Estimation Service using PrusaSlicer"
API_VERSION = "1.2.0"

# CORS settings
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")


def _env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


# --- Authentication (opt-in) ---------------------------------------------
# Comma-separated API keys. Empty list => authentication disabled (default).
API_KEYS = [k.strip() for k in os.getenv("API_KEYS", "").split(",") if k.strip()]

# --- Rate limiting (opt-in) ----------------------------------------------
# Max /slice requests per minute per client (API key, else IP). 0 => disabled.
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "0"))

# --- Concurrency cap ------------------------------------------------------
# Max simultaneous slices. 0 => unlimited.
MAX_CONCURRENT_SLICES = int(os.getenv("MAX_CONCURRENT_SLICES", "0"))

# --- Disk guard -----------------------------------------------------------
# Refuse new slices when free space in the work dir is below this (MB).
# 0 => disabled.
MIN_FREE_DISK_MB = int(os.getenv("MIN_FREE_DISK_MB", "0"))

# --- Slicing history (opt-in) --------------------------------------------
# Persist a record of each slice (parameters + results, never model files).
HISTORY_ENABLED = _env_bool("HISTORY_ENABLED", False)
HISTORY_DB_PATH = Path(os.getenv("HISTORY_DB_PATH", "/srv/data/history.db"))

# --- Async jobs -----------------------------------------------------------
# Number of finished jobs to retain in the in-memory store.
JOB_RETENTION = int(os.getenv("JOB_RETENTION", "100"))
