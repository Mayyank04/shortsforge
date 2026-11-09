"""
Metadata schemas and validated data models for ShortForge AI Minecraft Story Studio.
Defines StoryProject, Character, Scene, CameraInstruction, CharacterAction, and AudioCue.
"""
from __future__ import annotations
from typing import Literal, Optional, List, Dict, Any
from pydantic import BaseModel, Field

MinecraftGenre = Literal[
    "emotional", "funny", "mystery", "horror",
    "adventure", "friendship", "betrayal", "survival",
    "unexpected_twist", "heroic_sacrifice", "rescue", "fantasy"
]

CameraShot = Literal[
    "extreme_close_up", "close_up", "medium_shot", "wide_shot",
    "establishing_shot", "low_angle", "high_angle", "over_the_shoulder",
    "tracking_shot", "orbit", "dolly_in", "dolly_out", "crane", "pan", "tilt", "pov"
]

CharacterActionType = Literal[
    "walking", "running", "jumping", "falling", "sitting", "turning",
    "waving", "pointing", "fighting", "crying", "celebrating",
    "looking_surprised", "looking_scared", "hugging", "reaching", "carrying"
]

EnvironmentBiome = Literal[
    "Village", "Forest", "Cave", "Mountain", "Nether", "Snow",
    "Desert", "Castle", "Underground_Mine", "Ocean", "Farm"
]

class CameraInstruction(BaseModel):
    shot: CameraShot = "medium_shot"
    movement: str = "slow_dolly_in"
    focus: str = "protagonist"
    pitch: float = 15.0
    yaw: float = 0.0
    distance: float = 4.5
    height_offset: float = 1.0

class CharacterAction(BaseModel):
    character_id: str
    action: CharacterActionType = "walking"
    emotion: str = "determined"
    position: list[float] = Field(default_factory=lambda: [0.0, 0.0, 0.0])
    target_position: Optional[list[float]] = None
    facing_angle: float = 0.0

class AudioCue(BaseModel):
    sound_type: str  # whoosh, thunder, footsteps, impact, heartbeat, explosion, magic
    time_offset: float = 0.0
    volume: float = 1.0

class SceneSpec(BaseModel):
    scene_number: int
    duration: float = 5.0
    narration: str
    characters: list[str] = Field(default_factory=list)
    environment: str = "Village"
    time_of_day: str = "day"  # dawn, day, dusk, night, storm
    camera: CameraInstruction = Field(default_factory=CameraInstruction)
    character_actions: list[CharacterAction] = Field(default_factory=list)
    lighting: str = "warm golden sunlight with soft ambient bounce"
    atmosphere: str = "dust particles drifting in the light"
    effects: list[str] = Field(default_factory=list)
    transition: str = "cut"
    image_prompt: str = ""
    animation_prompt: str = ""
    audio_cues: list[str] = Field(default_factory=list)

class CanonicalCharacter(BaseModel):
    id: str
    name: str
    role: str = "protagonist"
    species: str = "villager"
    skin_tone: str = "#d49b6a"
    clothing_primary: str = "#2563eb"
    clothing_secondary: str = "#1e293b"
    hair_style: str = "short"
    hair_color: str = "#451a03"
    proportions: dict[str, float] = Field(
        default_factory=lambda: {"head": 1.0, "torso": 1.0, "arms": 1.0, "legs": 1.0, "height": 1.8}
    )
    personality: str = "Kind and determined"
    voice_preference: str = "heart"
    model_spec: dict[str, Any] = Field(default_factory=dict)
    reference_image_path: Optional[str] = None

class StoryProject(BaseModel):
    id: str
    title: str
    genre: MinecraftGenre = "adventure"
    duration: int = 50
    language: str = "en"
    voice: str = "heart"
    visual_quality: str = "final"
    viral_title: str = ""
    opening_hook: str = ""
    plot_summary: str = ""
    full_script: str = ""
    characters: list[CanonicalCharacter] = Field(default_factory=list)
    scenes: list[SceneSpec] = Field(default_factory=list)
    loop_opportunity: str = ""
    fingerprint: str = ""
