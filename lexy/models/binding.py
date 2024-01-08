from datetime import datetime
from enum import Enum
from typing import Any, Optional

from sqlalchemy import Column, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import SQLModel, Field, Relationship

from lexy.models.collection import Collection
from lexy.models.index import Index
from lexy.models.transformer import Transformer
from lexy.schemas.filters import Filter


class BindingStatus(str, Enum):
    PENDING = "pending"
    ON = "on"
    OFF = "off"
    DETACHED = "detached"


class BindingBase(SQLModel):
    # TODO: update ON DELETE behavior to switch to "detached" instead of deleting
    collection_id: str = Field(
        sa_column_args=(ForeignKey('collections.collection_id', ondelete='CASCADE'),),
        default="default",
        nullable=True
    )
    transformer_id: str = Field(default=None, foreign_key="transformers.transformer_id")
    # TODO: update ON DELETE behavior to switch to "detached" instead of deleting
    index_id: str = Field(
        sa_column_args=(ForeignKey('indexes.index_id', ondelete='CASCADE'),),
        default=None,
        nullable=True
    )

    description: Optional[str] = None
    execution_params: dict[str, Any] = Field(default={}, sa_column=Column(JSONB, nullable=False))
    transformer_params: dict[str, Any] = Field(default={}, sa_column=Column(JSONB, nullable=False))
    filter: Optional[Filter] = Field(default=None, sa_column=Column(JSONB, nullable=True))
    # # TODO: make this ENUM
    # run_frequency: str = Field(default="daily", nullable=False)


class Binding(BindingBase, table=True):
    __tablename__ = "bindings"
    binding_id: int = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()),
    )
    status: str = Field(default=BindingStatus.PENDING, nullable=False)
    collection: Collection = Relationship(back_populates="bindings", sa_relationship_kwargs={'lazy': 'selectin'})
    transformer: Transformer = Relationship(back_populates="bindings", sa_relationship_kwargs={'lazy': 'selectin'})
    index: Index = Relationship(back_populates="bindings", sa_relationship_kwargs={'lazy': 'selectin'})

    def __repr__(self):
        return f"<Binding(" \
               f"id={self.binding_id}, " \
               f"status={self.status}, " \
               f"collection='{self.collection_id}', " \
               f"transformer='{self.transformer_id}', " \
               f"index='{self.index_id}')>"


class BindingCreate(BindingBase):
    pass


class BindingUpdate(BindingBase):
    description: Optional[str] = None
    execution_params: Optional[dict[str, Any]] = None
    transformer_params: Optional[dict[str, Any]] = None
    filter: Optional[Filter] = None
    status: Optional[str] = None


class BindingRead(BindingBase):
    binding_id: int
    created_at: datetime
    updated_at: datetime
    status: str
    collection: Collection
    transformer: Transformer
    index: Index
    filter: Optional[Filter]
