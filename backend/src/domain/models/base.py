"""Base domain model for DCIS entities."""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class DomainEntity(BaseModel):
    """Base class for all domain entities."""

    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic configuration."""

        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class ValueObject(BaseModel):
    """Base class for value objects (immutable)."""

    class Config:
        """Pydantic configuration."""

        frozen = True
