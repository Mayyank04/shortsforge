from __future__ import annotations
from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Float, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

class Job(Base):
    __tablename__ = "jobs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    topic: Mapped[str] = mapped_column(String(500), nullable=False)
    style: Mapped[str] = mapped_column(String(40), default="geo_realistic")
    duration: Mapped[int] = mapped_column(Integer, default=75)
    voice: Mapped[str] = mapped_column(String(50), default="heart")
    preview: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(30), default="queued")
    output_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    logs: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

class MinecraftProject(Base):
    __tablename__ = "minecraft_projects"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    genre: Mapped[str] = mapped_column(String(50), default="adventure")
    duration: Mapped[int] = mapped_column(Integer, default=50)
    language: Mapped[str] = mapped_column(String(10), default="en")
    voice: Mapped[str] = mapped_column(String(50), default="heart")
    visual_quality: Mapped[str] = mapped_column(String(20), default="final")
    status: Mapped[str] = mapped_column(String(30), default="draft")
    viral_title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    opening_hook: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    plot_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    full_script: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    story_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    output_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    logs: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    scenes: Mapped[List["MinecraftScene"]] = relationship("MinecraftScene", back_populates="project", cascade="all, delete-orphan", order_by="MinecraftScene.scene_number")

class MinecraftCharacter(Base):
    __tablename__ = "minecraft_characters"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="protagonist")
    species: Mapped[str] = mapped_column(String(50), default="villager")
    skin_tone: Mapped[str] = mapped_column(String(20), default="#d49b6a")
    clothing_primary: Mapped[str] = mapped_column(String(20), default="#2563eb")
    clothing_secondary: Mapped[str] = mapped_column(String(20), default="#1e293b")
    hair_style: Mapped[str] = mapped_column(String(50), default="short")
    hair_color: Mapped[str] = mapped_column(String(20), default="#451a03")
    proportions_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    personality: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    voice_preference: Mapped[str] = mapped_column(String(50), default="heart")
    model_spec_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reference_image_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

class MinecraftScene(Base):
    __tablename__ = "minecraft_scenes"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("minecraft_projects.id", ondelete="CASCADE"), nullable=False)
    scene_number: Mapped[int] = mapped_column(Integer, nullable=False)
    duration: Mapped[float] = mapped_column(Float, default=5.0)
    narration: Mapped[str] = mapped_column(Text, nullable=False)
    characters_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    environment: Mapped[str] = mapped_column(String(100), default="Village")
    time_of_day: Mapped[str] = mapped_column(String(30), default="day")
    camera_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    character_actions_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    lighting: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    atmosphere: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    vfx_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    transition: Mapped[str] = mapped_column(String(50), default="cut")
    image_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    animation_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    audio_cues_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rendered_frame_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    project: Mapped["MinecraftProject"] = relationship("MinecraftProject", back_populates="scenes")

class StoryHistory(Base):
    __tablename__ = "story_history"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    genre: Mapped[str] = mapped_column(String(50), nullable=False)
    fingerprint: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
