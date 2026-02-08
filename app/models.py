"""Pydantic models for request/response validation"""
from pydantic import BaseModel, Field
from typing import Optional


class SliceRequest(BaseModel):
    """Request model for slicing parameters"""
    layer_height: float = Field(
        default=0.2, 
        ge=0.1, 
        le=0.4, 
        description="Layer height in mm"
    )
    infill_density: int = Field(
        default=15, 
        ge=0, 
        le=100, 
        description="Infill percentage"
    )
    wall_count: int = Field(
        default=2, 
        ge=1, 
        le=10, 
        description="Number of perimeter walls"
    )
    filament_type: str = Field(
        default="PLA", 
        description="Filament type"
    )
    filament_density: Optional[float] = Field(
        default=None, 
        description="Custom filament density (g/cm³)"
    )


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
