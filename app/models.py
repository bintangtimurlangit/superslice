"""Pydantic models for request/response validation."""
from pydantic import BaseModel


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
