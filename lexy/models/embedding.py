from datetime import datetime
from typing import Any, List, Optional
from uuid import uuid4, UUID

from sqlalchemy import Column, DateTime, DDL, event, func, REAL
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import ARRAY, Field, Relationship, SQLModel

from lexy.models.document import Document


class EmbeddingBase(SQLModel):
    document_id: UUID = Field(foreign_key="documents.document_id", index=True)
    embedding: List[float] = Field(sa_column=Column(ARRAY(REAL)))
    text: Optional[str] = Field(default=None)
    meta: Optional[dict[Any, Any]] = Field(sa_column=Column(JSONB), default={})
    custom_id: Optional[str] = Field(default=None)


class Embedding(EmbeddingBase, table=True):
    __tablename__ = "embeddings"

    embedding_id: UUID = Field(
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
    document: Document = Relationship(back_populates="embeddings")
    task_id: Optional[UUID] = Field(default=None)


class EmbeddingCreate(EmbeddingBase):
    pass


class EmbeddingUpdate(EmbeddingBase):
    embedding: Optional[List[float]] = None
    text: Optional[str] = None
    meta: Optional[dict[Any, Any]] = None
    custom_id: Optional[str] = None


embeddings_table = SQLModel.metadata.tables.get(Embedding.__tablename__)
event.listen(
    embeddings_table,
    "after_create",
    DDL(
        f"CREATE INDEX IF NOT EXISTS ix_{Embedding.__tablename__}_embedding_hnsw "
        f"ON {Embedding.__tablename__} "
        f"USING hnsw (embedding) "
        f"WITH (dims = 384, m = 8, efconstruction = 16, efsearch = 16);"
    ),
)
