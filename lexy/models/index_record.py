from datetime import datetime
from typing import Any, Optional, TYPE_CHECKING
from uuid import uuid4, UUID

from sqlalchemy import Column, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from lexy.models.document import Document


class IndexRecordBase(SQLModel):
    document_id: Optional[UUID] = Field(
        sa_column_args=(ForeignKey('documents.document_id', ondelete='CASCADE'),),
        index=True,
        nullable=True
    )
    custom_id: Optional[str] = Field(default=None)
    meta: Optional[dict[Any, Any]] = Field(sa_column=Column(JSONB), default={})


class IndexRecordCreate(IndexRecordBase):
    pass


class IndexRecordUpdate(IndexRecordBase):
    custom_id: Optional[str] = None
    meta: Optional[dict[Any, Any]] = None


class IndexRecordBaseTable(IndexRecordBase):
    index_record_id: UUID = Field(
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
    document: "Document" = Relationship(back_populates="index_records")
    task_id: Optional[UUID] = Field(default=None)

