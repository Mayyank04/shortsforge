from __future__ import annotations
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column
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
