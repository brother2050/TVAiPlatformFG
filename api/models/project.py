"""Project and Episode ORM models + Pydantic schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, model_validator
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.models.base import Base


# ---------------------------------------------------------------------------
# SQLAlchemy ORM Models
# ---------------------------------------------------------------------------

class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(200))
    genre: Mapped[str] = mapped_column(String(50))
    style: Mapped[str] = mapped_column(String(50))
    total_episodes: Mapped[int] = mapped_column(Integer, default=10)
    episode_duration_sec: Mapped[int] = mapped_column(Integer, default=120)
    global_settings: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    episodes: Mapped[list["Episode"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    characters: Mapped[list] = relationship("Character", back_populates="project", cascade="all, delete-orphan")
    summaries: Mapped[list] = relationship("Summary", back_populates="project", cascade="all, delete-orphan")


class Episode(Base):
    __tablename__ = "episodes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"))
    episode_number: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(200))
    synopsis: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="episodes")
    scenes: Mapped[list] = relationship("Scene", back_populates="episode", cascade="all, delete-orphan")
    production_tasks: Mapped[list] = relationship("ProductionTask", back_populates="episode", cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------

class ProjectGlobalSettings(BaseModel):
    genre: str = ""                    # 题材/类型: 都市、古装、科幻、玄幻、悬疑、喜剧、爱情、动作、冒险、奇幻、自定义
    art_style: str = ""                # 画风: 日系动漫、写实、水彩、像素、赛博朋克、国风、欧美卡通、二次元、3D渲染、自定义
    color_palette: str = ""
    narrative_pace: str = ""
    target_audience: str = ""
    overall_mood: str = ""
    music_style: str = ""
    subtitle_style: str = ""
    custom_dimensions: dict[str, str] = Field(default_factory=dict)
    global_prompt_prefix: str = ""

    @model_validator(mode='before')
    @classmethod
    def fill_defaults(cls, values):
        if isinstance(values, dict):
            defaults = {
                'genre': '',
                'art_style': '',
                'color_palette': '',
                'narrative_pace': '',
                'target_audience': '',
                'overall_mood': '',
                'music_style': '',
                'subtitle_style': '',
                'custom_dimensions': {},
                'global_prompt_prefix': '',
            }
            for key, default in defaults.items():
                if key not in values:
                    values[key] = default
        return values


class ProjectCreate(BaseModel):
    title: str
    genre: str = ""
    style: str = ""
    total_episodes: int = 10
    episode_duration_sec: int = 120
    global_settings: ProjectGlobalSettings = Field(default_factory=ProjectGlobalSettings)


class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    genre: Optional[str] = None
    style: Optional[str] = None
    total_episodes: Optional[int] = None
    episode_duration_sec: Optional[int] = None
    global_settings: Optional[ProjectGlobalSettings] = None
    status: Optional[str] = None


class ProjectOut(BaseModel):
    id: str
    title: str
    genre: str
    style: str
    total_episodes: int
    episode_duration_sec: int
    global_settings: dict[str, Any]
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EpisodeCreate(BaseModel):
    episode_number: int
    title: str
    synopsis: str = ""


class EpisodeUpdate(BaseModel):
    title: Optional[str] = None
    synopsis: Optional[str] = None
    status: Optional[str] = None
    episode_number: Optional[int] = None


class EpisodeOut(BaseModel):
    id: str
    project_id: str
    episode_number: int
    title: str
    synopsis: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
