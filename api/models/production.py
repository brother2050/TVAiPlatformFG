"""ProductionTask ORM model + Pydantic schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field
from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.models.base import Base


# ---------------------------------------------------------------------------
# SQLAlchemy ORM Model
# ---------------------------------------------------------------------------

class ProductionTask(Base):
    __tablename__ = "production_tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    episode_id: Mapped[str] = mapped_column(String(36), ForeignKey("episodes.id", ondelete="CASCADE"))
    stage: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    assets: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    review_notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    episode: Mapped["Episode"] = relationship(back_populates="production_tasks")


# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------

class ProductionTaskOut(BaseModel):
    id: str
    episode_id: str
    stage: str
    status: str
    assets: dict[str, Any]
    review_notes: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProductionProgress(BaseModel):
    episode_id: str
    stages: list[dict[str, Any]] = Field(default_factory=list)
    overall_progress: float = 0.0
