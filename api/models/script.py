"""Scene and Shot ORM models + Pydantic schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.models.base import Base


# ---------------------------------------------------------------------------
# SQLAlchemy ORM Models
# ---------------------------------------------------------------------------

class Scene(Base):
    __tablename__ = "scenes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    episode_id: Mapped[str] = mapped_column(String(36), ForeignKey("episodes.id", ondelete="CASCADE"))
    scene_number: Mapped[int] = mapped_column(Integer)
    location: Mapped[str] = mapped_column(String(200), default="")
    time_of_day: Mapped[str] = mapped_column(String(50), default="day")
    weather: Mapped[str] = mapped_column(String(50), default="clear")
    atmosphere: Mapped[str] = mapped_column(String(100), default="")
    characters_present: Mapped[list[str]] = mapped_column(JSONB, default=list)
    background_music: Mapped[str] = mapped_column(Text, default="")
    ambient_sound: Mapped[str] = mapped_column(Text, default="")
    scene_overrides: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    episode: Mapped["Episode"] = relationship(back_populates="scenes")
    shots: Mapped[list["Shot"]] = relationship(back_populates="scene", cascade="all, delete-orphan")


class Shot(Base):
    __tablename__ = "shots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scene_id: Mapped[str] = mapped_column(String(36), ForeignKey("scenes.id", ondelete="CASCADE"))
    shot_number: Mapped[int] = mapped_column(Integer)
    shot_type: Mapped[str] = mapped_column(String(20), default="medium")
    camera_movement: Mapped[str] = mapped_column(String(20), default="static")
    duration_sec: Mapped[float] = mapped_column(Float, default=3.0)
    visual_description: Mapped[str] = mapped_column(Text, default="")
    character_actions: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    character_positions: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    dialogues: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
    narration: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    emotion_tags: Mapped[list[str]] = mapped_column(JSONB, default=list)
    character_emotions: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)

    # Relationships
    scene: Mapped["Scene"] = relationship(back_populates="shots")


# ---------------------------------------------------------------------------
# Pydantic Schemas — inline models
# ---------------------------------------------------------------------------

class Position(BaseModel):
    x: float = 0.5
    y: float = 0.5
    depth: float = 0.0
    facing: str = "center"


class Dialogue(BaseModel):
    id: str = ""
    character_id: str = ""
    text: str = ""
    emotion: str = "calm"
    volume: str = "normal"
    pace: str = "normal"
    pause_after_sec: float = 0.0
    overlap_with_previous: bool = False


class SceneCreate(BaseModel):
    scene_number: int
    location: str = ""
    time_of_day: str = "day"
    weather: str = "clear"
    atmosphere: str = ""
    characters_present: list[str] = Field(default_factory=list)
    background_music: str = ""
    ambient_sound: str = ""


class SceneUpdate(BaseModel):
    scene_number: Optional[int] = None
    location: Optional[str] = None
    time_of_day: Optional[str] = None
    weather: Optional[str] = None
    atmosphere: Optional[str] = None
    characters_present: Optional[list[str]] = None
    background_music: Optional[str] = None
    ambient_sound: Optional[str] = None
    scene_overrides: Optional[dict[str, Any]] = None


class ShotUpdate(BaseModel):
    shot_type: Optional[str] = None
    camera_movement: Optional[str] = None
    duration_sec: Optional[float] = None
    visual_description: Optional[str] = None
    character_actions: Optional[dict[str, Any]] = None
    character_positions: Optional[dict[str, Any]] = None
    dialogues: Optional[list[dict[str, Any]]] = None
    narration: Optional[str] = None
    emotion_tags: Optional[list[str]] = None
    character_emotions: Optional[dict[str, Any]] = None


class ShotOut(BaseModel):
    id: str
    scene_id: str
    shot_number: int
    shot_type: str
    camera_movement: str
    duration_sec: float
    visual_description: str
    character_actions: dict[str, Any]
    character_positions: dict[str, Any]
    dialogues: list[dict[str, Any]]
    narration: Optional[str]
    emotion_tags: list[str]
    character_emotions: dict[str, Any]

    model_config = {"from_attributes": True}


class SceneOut(BaseModel):
    id: str
    episode_id: str
    scene_number: int
    location: str
    time_of_day: str
    weather: str
    atmosphere: str
    characters_present: list[str]
    background_music: str
    ambient_sound: str
    scene_overrides: Optional[dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    shots: list[ShotOut] = Field(default_factory=list)

    model_config = {"from_attributes": True}
