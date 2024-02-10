from datetime import datetime
from typing import Any, Optional, TYPE_CHECKING

from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import SQLModel, Field, Relationship

from lexy.core.config import settings

if TYPE_CHECKING:
    from lexy.models.binding import Binding
    from lexy.models.document import Document


class CollectionBase(SQLModel):
    collection_id: str = Field(
        default=None,
        primary_key=True,
        min_length=1,
        max_length=255,
        regex=r"^[A-Za-z0-9_-]+$"
    )
    description: Optional[str] = None
    config: Optional[dict[str, Any]] = Field(sa_column=Column(JSONB), default=settings.COLLECTION_DEFAULT_CONFIG)


class Collection(CollectionBase, table=True):
    __tablename__ = "collections"
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()),
    )
    documents: list["Document"] = Relationship(
        back_populates="collection",
        sa_relationship_kwargs={'lazy': 'select'}
    )
    bindings: list["Binding"] = Relationship(
        back_populates="collection",
        sa_relationship_kwargs={'lazy': 'selectin', 'cascade': 'all, delete-orphan'}
    )


class CollectionCreate(CollectionBase):
    pass


class CollectionUpdate(CollectionBase):
    description: Optional[str] = None
    config: Optional[dict[str, Any]] = None
