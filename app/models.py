"""Pydantic models for request/response validation."""
from typing import Any, List, Optional

from pydantic import BaseModel, Field


class SliceResponse(BaseModel):
    """Response model with slicing results."""
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

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "print_time_minutes": 45.5,
                "print_time_formatted": "45m 30s",
                "filament_length_mm": 1234.56,
                "filament_volume_cm3": 2.98,
                "filament_weight_g": 3.69,
                "filament_type": "PLA",
                "layer_height": 0.2,
                "infill_density": 20,
                "wall_count": 3,
            }
        }
    }


class ErrorDetail(BaseModel):
    """Machine-readable part of an error response."""
    code: str = Field(..., examples=["FILE_TOO_LARGE"])
    message: str = Field(..., examples=["File exceeds maximum size of 104857600 bytes"])


class ErrorResponse(BaseModel):
    """Consistent error envelope returned for every 4xx/5xx response."""
    detail: Any = Field(..., description="Human-readable message (kept for compatibility)")
    error: ErrorDetail


class VersionInfo(BaseModel):
    """Service and bundled-slicer versions."""
    service: str
    version: str
    slicer: str


class JobCreated(BaseModel):
    """Returned by POST /jobs when a slice is accepted for async processing."""
    job_id: str
    status: str
    status_url: str


class JobStatusResponse(BaseModel):
    """State of an async slice job."""
    job_id: str
    status: str  # pending | running | succeeded | failed
    created_at: float
    finished_at: Optional[float] = None
    result: Optional[SliceResponse] = None
    error: Optional[ErrorDetail] = None


class HistoryItem(BaseModel):
    """A persisted record of a past slice (no model files are stored)."""
    id: int
    created_at: str
    filename: Optional[str] = None
    layer_height: float
    infill_density: int
    wall_count: int
    filament_type: str
    print_time_seconds: int
    filament_length_mm: float
    filament_volume_cm3: float
    filament_weight_g: float


class HistoryList(BaseModel):
    """A page of history records."""
    count: int
    items: List[HistoryItem]
