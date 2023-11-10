from datetime import datetime
from enum import Enum
from typing import Any, Optional

from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import SQLModel, Field, Relationship

from lexy.models.collection import Collection
from lexy.models.index import Index
from lexy.models.transformer import Transformer


class BindingStatus(str, Enum):
    PENDING = "pending"
    ON = "on"
    OFF = "off"
    DETACHED = "detached"


class TransformerIndexBindingBase(SQLModel):
    collection_id: str = Field(default="default", foreign_key="collections.collection_id")
    transformer_id: str = Field(default=None, foreign_key="transformers.transformer_id")
    index_id: str = Field(default=None, foreign_key="indexes.index_id")

    description: Optional[str] = None
    execution_params: dict[str, Any] = Field(default={}, sa_column=Column(JSONB, nullable=False))
    transformer_params: dict[str, Any] = Field(default={}, sa_column=Column(JSONB, nullable=False))
    filters = Field(default={}, sa_column=Column(JSONB, nullable=False))
    # # TODO: make this ENUM
    # run_frequency: str = Field(default="daily", nullable=False)


class TransformerIndexBinding(TransformerIndexBindingBase, table=True):
    __tablename__ = "transformer_index_bindings"
    binding_id: int = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()),
    )
    status: str = Field(default=BindingStatus.PENDING, nullable=False)
    collection: Collection = Relationship(back_populates="transformer_index_bindings",
                                          sa_relationship_kwargs={'lazy': 'selectin'})
    transformer: Transformer = Relationship(back_populates="index_bindings",
                                            sa_relationship_kwargs={'lazy': 'selectin'})
    index: Index = Relationship(back_populates="transformer_bindings", sa_relationship_kwargs={'lazy': 'selectin'})

    def __repr__(self):
        return f"<Binding(" \
               f"id={self.binding_id}, " \
               f"status={self.status}, " \
               f"collection='{self.collection_id}', " \
               f"transformer='{self.transformer_id}', " \
               f"index='{self.index_id}')>"


class TransformerIndexBindingCreate(TransformerIndexBindingBase):
    pass


class TransformerIndexBindingUpdate(TransformerIndexBindingBase):
    description: Optional[str] = None
    execution_params: Optional[dict[str, Any]] = None
    transformer_params: Optional[dict[str, Any]] = None
    filters: Optional[dict[str, Any]] = None
    status: Optional[str] = None


class TransformerIndexBindingRead(TransformerIndexBindingBase):
    binding_id: int
    created_at: datetime
    updated_at: datetime
    status: str
    collection: Collection
    transformer: Transformer
    index: Index

