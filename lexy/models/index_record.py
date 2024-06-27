from datetime import datetime
from typing import Any, Optional
from uuid import uuid4, UUID

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql.schema import Table
from sqlmodel import SQLModel, Field


# Fields requiring SQLAlchemy objects (Column or ForeignKey) have been moved to IndexManager until SQLModel fixes
#   inheritance for Pydantic V2+


class IndexRecordBase(SQLModel):
    document_id: Optional[UUID] = Field(
        foreign_key="documents.document_id", index=True, nullable=True
    )
    custom_id: Optional[str] = Field(default=None)
    meta: Optional[dict[Any, Any]] = Field(default={}, sa_type=JSONB)


class IndexRecordCreate(IndexRecordBase):
    pass


class IndexRecordUpdate(IndexRecordBase):
    custom_id: Optional[str] = None
    meta: Optional[dict[Any, Any]] = None


class IndexRecordBaseTable(IndexRecordBase):
    __table__: Table | None = None
    index_record_id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )
    # `created_at` and `updated_at` are hacked to use sa_type along with kwargs -- will update once SQLModel
    #    inheritance is fixed
    created_at: datetime = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore
        sa_column_kwargs=dict(nullable=False, server_default=func.now()),
    )
    updated_at: datetime = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore
        sa_column_kwargs=dict(
            nullable=False, server_default=func.now(), onupdate=func.now()
        ),
    )
    task_id: Optional[UUID] = Field(default=None)
    binding_id: Optional[int] = Field(
        foreign_key="bindings.binding_id", index=True, nullable=True
    )
