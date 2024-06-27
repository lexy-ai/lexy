from datetime import datetime
from typing import Any, Optional, TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import Column, DateTime, func, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import SQLModel, Field, Relationship

from lexy.core.config import settings

if TYPE_CHECKING:
    from lexy.models.binding import Binding
    from lexy.models.document import Document


def generate_short_uid() -> str:
    return uuid4().hex[:8]


class CollectionBase(SQLModel):
    collection_name: str = Field(
        unique=True,
        min_length=1,
        max_length=56,
        # Postgres identifiers are limited to 63 characters (so 63 - len('zzcol__') = 56)
        # TODO: switch back to `regex=` (or `pattern=`) once SQLModel bug is fixed
        #   https://github.com/tiangolo/sqlmodel/discussions/735
        schema_extra={"pattern": r"^[a-z_][a-z0-9_]{0,55}$"},
    )
    description: Optional[str] = None
    config: Optional[dict[str, Any]] = Field(
        sa_column=Column(JSONB), default=settings.COLLECTION_DEFAULT_CONFIG
    )


class Collection(CollectionBase, table=True):
    __tablename__ = "collections"
    collection_id: str = Field(
        default=None,
        sa_column=Column(
            String(length=8), default=generate_short_uid, primary_key=True, unique=True
        ),
    )
    created_at: datetime = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True), nullable=False, server_default=func.now()
        ),
    )
    updated_at: datetime = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            server_default=func.now(),
            onupdate=func.now(),
        ),
    )
    documents: list["Document"] = Relationship(
        back_populates="collection", sa_relationship_kwargs={"lazy": "select"}
    )
    bindings: list["Binding"] = Relationship(
        back_populates="collection",
        sa_relationship_kwargs={"lazy": "selectin", "cascade": "all, delete-orphan"},
    )


class CollectionCreate(CollectionBase):
    pass


class CollectionUpdate(CollectionBase):
    collection_name: Optional[str] = Field(
        default=None,
        unique=True,
        min_length=1,
        max_length=56,
        # Postgres identifiers are limited to 63 characters (so 63 - len('zzcol__') = 56)
        # TODO: switch back to `regex=` (or `pattern=`) once SQLModel bug is fixed
        #   https://github.com/tiangolo/sqlmodel/discussions/735
        schema_extra={"pattern": r"^[a-z_][a-z0-9_]{0,55}$"},
    )
    description: Optional[str] = None
    config: Optional[dict[str, Any]] = None
