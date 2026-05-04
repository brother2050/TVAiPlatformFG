"""JSONTemplate ORM model + Pydantic schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field
from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from api.models.base import Base


# ---------------------------------------------------------------------------
# SQLAlchemy ORM Model
# ---------------------------------------------------------------------------

class JSONTemplate(Base):
    __tablename__ = "templates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100))
    slug: Mapped[str] = mapped_column(String(50), unique=True)
    category: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(Text, default="")
    schema_definition: Mapped[dict[str, Any]] = mapped_column("schema", JSONB, default=dict)
    example: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    system_prompt_suffix: Mapped[str] = mapped_column(Text, default="")
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_builtin: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------

class TemplateCreate(BaseModel):
    name: str
    slug: str
    category: str
    description: str = ""
    schema_definition: dict[str, Any] = Field(default_factory=dict)
    example: dict[str, Any] = Field(default_factory=dict)
    system_prompt_suffix: str = ""


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    schema_definition: Optional[dict[str, Any]] = None
    example: Optional[dict[str, Any]] = None
    system_prompt_suffix: Optional[str] = None


class TemplateOut(BaseModel):
    id: str
    name: str
    slug: str
    category: str
    description: str
    schema_definition: dict[str, Any]
    example: dict[str, Any]
    system_prompt_suffix: str
    version: int
    is_builtin: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
