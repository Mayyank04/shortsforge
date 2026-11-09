from __future__ import annotations
from pydantic import BaseModel, Field, ConfigDict
from typing import Literal, Optional
from datetime import datetime

Style = Literal[
    "mixed", "2d", "3d",
    "geo_realistic", "geo_political", "geo_terrain", "geo_historical"
]

class JobCreate(BaseModel):
    topic: str = Field(min_length=4, max_length=500)
    style: Style = "geo_realistic"
    duration: int = Field(default=75, ge=15, le=120)
    voice: str = "heart"
    preview: bool = False

class BatchJobCreate(BaseModel):
    jobs: list[JobCreate]

class JobStatusUpdate(BaseModel):
    status: Literal[
        "queued", "running", "researching", "scripting",
        "generating_voice", "rendering_3d", "assembling",
        "completed", "failed", "cancelled"
    ]
    output_path: Optional[str] = None
    error: Optional[str] = None
    logs: Optional[str] = None
    metadata_json: Optional[str] = None

class JobOut(BaseModel):
    id: str
    topic: str
    style: str
    duration: int
    voice: str = "heart"
    preview: bool = False
    status: str
    output_path: Optional[str] = None
    error: Optional[str] = None
    logs: Optional[str] = None
    metadata_json: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
