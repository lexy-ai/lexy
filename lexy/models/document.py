from datetime import datetime
from typing import Optional, Any
from uuid import uuid4, UUID

from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel, Relationship

from lexy.models.collection import Collection


class DocumentBase(SQLModel):
    title: str
    content: str
    meta: Optional[dict[Any, Any]] = Field(sa_column=Column(JSONB), default={})


class Document(DocumentBase, table=True):
    __tablename__ = "documents"
    document_id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()),
    )
    collection_id: str = Field(default="default", foreign_key="collections.collection_id")
    collection: Collection = Relationship(back_populates="documents", sa_relationship_kwargs={'lazy': 'selectin'})
    embeddings: list["Embedding"] = Relationship(back_populates="document")


class DocumentCreate(DocumentBase):
    pass


class DocumentUpdate(DocumentBase):
    title: Optional[str] = None
    content: Optional[str] = None
    meta: Optional[dict[Any, Any]] = None


# class DocumentInDB(DocumentBase):
#     pass
