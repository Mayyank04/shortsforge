from __future__ import annotations
from pydantic import BaseModel, Field, ConfigDict
from typing import Literal, Optional, Any
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

# -------------------------------------------------------------
# Minecraft Story Studio Schemas
# -------------------------------------------------------------

MinecraftGenre = Literal[
    "emotional", "funny", "mystery", "horror",
    "adventure", "friendship", "betrayal", "survival",
    "unexpected_twist", "heroic_sacrifice", "rescue", "fantasy"
]

class MinecraftSceneOut(BaseModel):
    id: str
    project_id: str
    scene_number: int
    duration: float
    narration: str
    characters_json: Optional[str] = None
    environment: str
    time_of_day: str
    camera_json: Optional[str] = None
    character_actions_json: Optional[str] = None
    lighting: Optional[str] = None
    atmosphere: Optional[str] = None
    vfx_json: Optional[str] = None
    transition: str = "cut"
    image_prompt: Optional[str] = None
    animation_prompt: Optional[str] = None
    audio_cues_json: Optional[str] = None
    rendered_frame_path: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class MinecraftSceneUpdate(BaseModel):
    duration: Optional[float] = None
    narration: Optional[str] = None
    characters_json: Optional[str] = None
    environment: Optional[str] = None
    time_of_day: Optional[str] = None
    camera_json: Optional[str] = None
    character_actions_json: Optional[str] = None
    lighting: Optional[str] = None
    atmosphere: Optional[str] = None
    vfx_json: Optional[str] = None
    transition: Optional[str] = None
    image_prompt: Optional[str] = None
    animation_prompt: Optional[str] = None
    audio_cues_json: Optional[str] = None

class MinecraftProjectCreate(BaseModel):
    title: str = Field(min_length=3, max_length=500)
    genre: MinecraftGenre = "adventure"
    duration: int = Field(default=50, ge=20, le=120)
    language: str = "en"
    voice: str = "heart"
    visual_quality: str = "final"
    characters: Optional[list[str]] = None
    custom_idea: Optional[str] = None
    auto_render: bool = False

class MinecraftProjectUpdate(BaseModel):
    title: Optional[str] = None
    genre: Optional[str] = None
    duration: Optional[int] = None
    language: Optional[str] = None
    voice: Optional[str] = None
    visual_quality: Optional[str] = None
    status: Optional[str] = None
    full_script: Optional[str] = None
    story_json: Optional[str] = None

class MinecraftProjectOut(BaseModel):
    id: str
    title: str
    genre: str
    duration: int
    language: str
    voice: str
    visual_quality: str
    status: str
    viral_title: Optional[str] = None
    opening_hook: Optional[str] = None
    plot_summary: Optional[str] = None
    full_script: Optional[str] = None
    story_json: Optional[str] = None
    output_path: Optional[str] = None
    error: Optional[str] = None
    logs: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    scenes: list[MinecraftSceneOut] = []
    model_config = ConfigDict(from_attributes=True)

class MinecraftCharacterCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    role: str = "protagonist"
    species: str = "villager"
    skin_tone: str = "#d49b6a"
    clothing_primary: str = "#2563eb"
    clothing_secondary: str = "#1e293b"
    hair_style: str = "short"
    hair_color: str = "#451a03"
    personality: Optional[str] = None
    voice_preference: str = "heart"
    proportions_json: Optional[str] = None
    model_spec_json: Optional[str] = None

class MinecraftCharacterUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    species: Optional[str] = None
    skin_tone: Optional[str] = None
    clothing_primary: Optional[str] = None
    clothing_secondary: Optional[str] = None
    hair_style: Optional[str] = None
    hair_color: Optional[str] = None
    personality: Optional[str] = None
    voice_preference: Optional[str] = None
    proportions_json: Optional[str] = None
    model_spec_json: Optional[str] = None

class MinecraftCharacterOut(BaseModel):
    id: str
    name: str
    role: str
    species: str
    skin_tone: str
    clothing_primary: str
    clothing_secondary: str
    hair_style: str
    hair_color: str
    personality: Optional[str] = None
    voice_preference: str
    proportions_json: Optional[str] = None
    model_spec_json: Optional[str] = None
    reference_image_path: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class StoryGenerateRequest(BaseModel):
    genre: MinecraftGenre = "adventure"
    idea: Optional[str] = None
    duration: int = Field(default=50, ge=20, le=120)
    language: str = "en"
    character_ids: Optional[list[str]] = None
    use_ollama: bool = True

class MinecraftRenderRequest(BaseModel):
    preview: bool = False
    resolution: Optional[str] = None
    fps: int = 30
