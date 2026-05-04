"""Summary ORM model + Pydantic schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.models.base import Base


# ---------------------------------------------------------------------------
# SQLAlchemy ORM Model
# ---------------------------------------------------------------------------

class Summary(Base):
    __tablename__ = "summaries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"))
    summary_type: Mapped[str] = mapped_column(String(20))
    episode_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    arc_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    content: Mapped[str] = mapped_column(Text, default="")
    extra_data: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="summaries")


# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------

class SummaryCreate(BaseModel):
    summary_type: str
    episode_number: Optional[int] = None
    arc_name: Optional[str] = None
    content: str = ""
    extra_data: dict[str, Any] = Field(default_factory=dict)


class SummaryOut(BaseModel):
    id: str
    project_id: str
    summary_type: str
    episode_number: Optional[int]
    arc_name: Optional[str]
    content: str
    extra_data: dict[str, Any]
    generated_at: datetime

    model_config = {"from_attributes": True}
