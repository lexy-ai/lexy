from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Column, DateTime, func
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from lexy.models.binding import Binding
    from lexy.models.document import Document


class CollectionBase(SQLModel):
    collection_id: str = Field(
        default=None,
        primary_key=True,
        min_length=1,
        max_length=255,
        regex=r"^[a-z0-9_-]+$"
    )
    description: Optional[str] = None


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
