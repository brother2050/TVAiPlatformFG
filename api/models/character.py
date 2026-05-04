"""Character ORM model + Pydantic schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field
from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.models.base import Base


# ---------------------------------------------------------------------------
# SQLAlchemy ORM Model
# ---------------------------------------------------------------------------

class Character(Base):
    __tablename__ = "characters"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(100))
    gender: Mapped[str] = mapped_column(String(20), default="other")
    appearance: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    body: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    voice: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    wardrobe_default: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    reference_images: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    consistency_seed: Mapped[int] = mapped_column(Integer, default=0)
    face_embedding: Mapped[list[float]] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="characters")


# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------

class AppearanceSpec(BaseModel):
    face_shape: str = ""
    eye_color: str = ""
    hair_style: str = ""
    hair_color: str = ""
    skin_tone: str = ""
    distinctive_features: list[str] = Field(default_factory=list)
    expression_bias: str = ""


class BodySpec(BaseModel):
    height_cm: float = 170.0
    weight_kg: float = 65.0
    body_type: str = "average"


class VoiceSpec(BaseModel):
    tone: str = ""
    speed: str = "normal"
    pitch: str = "normal"


class WardrobeSpec(BaseModel):
    top: str = ""
    bottom: str = ""
    shoes: str = ""
    color_palette: list[str] = Field(default_factory=list)


class CharacterCreate(BaseModel):
    name: str
    gender: str = "other"
    appearance: AppearanceSpec = Field(default_factory=AppearanceSpec)
    body: BodySpec = Field(default_factory=BodySpec)
    voice: VoiceSpec = Field(default_factory=VoiceSpec)
    wardrobe_default: WardrobeSpec = Field(default_factory=WardrobeSpec)


class CharacterUpdate(BaseModel):
    name: Optional[str] = None
    gender: Optional[str] = None
    appearance: Optional[AppearanceSpec] = None
    body: Optional[BodySpec] = None
    voice: Optional[VoiceSpec] = None
    wardrobe_default: Optional[WardrobeSpec] = None
    consistency_seed: Optional[int] = None


class CharacterOut(BaseModel):
    id: str
    project_id: str
    name: str
    gender: str
    appearance: dict[str, Any]
    body: dict[str, Any]
    voice: dict[str, Any]
    wardrobe_default: dict[str, Any]
    reference_images: dict[str, Any]
    consistency_seed: int
    face_embedding: list[float]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
