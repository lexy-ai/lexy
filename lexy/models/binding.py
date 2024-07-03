from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import model_validator
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


# Shared properties
class BindingBase(SQLModel):
    collection_id: Optional[str] = None
    transformer_id: str = Field(
        foreign_key="transformers.transformer_id", default=None, nullable=True
    )
    index_id: str = Field(
        sa_column_args=(ForeignKey("indexes.index_id", ondelete="CASCADE"),),
        default=None,
        nullable=True,
    )
    description: Optional[str] = None
    execution_params: dict[str, Any] = Field(
        default={}, sa_column=Column(JSONB, nullable=False)
    )
    transformer_params: dict[str, Any] = Field(
        default={}, sa_column=Column(JSONB, nullable=False)
    )
    filter: Optional[Filter] = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )


class Binding(BindingBase, table=True):
    __tablename__ = "bindings"
    binding_id: int = Field(default=None, primary_key=True)
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
    status: str = Field(default=BindingStatus.PENDING, nullable=False)
    collection_id: str = Field(
        sa_column_args=(ForeignKey("collections.collection_id", ondelete="CASCADE"),),
    )
    collection: "Collection" = Relationship(
        back_populates="bindings", sa_relationship_kwargs={"lazy": "selectin"}
    )
    transformer: Transformer = Relationship(
        back_populates="bindings", sa_relationship_kwargs={"lazy": "selectin"}
    )
    index: Index = Relationship(
        back_populates="bindings", sa_relationship_kwargs={"lazy": "selectin"}
    )

    def __repr__(self):
        return (
            f"<Binding("
            f"id={self.binding_id}, "
            f"status={self.status}, "
            f"collection='{self.collection_id}', "
            f"transformer='{self.transformer_id}', "
            f"index='{self.index_id}')>"
        )

    @property
    def filter_obj(self):
        if self.filter is not None:
            return Filter.model_validate(self.filter)
        return None


# Passed to the API from the client, can use name or id
class BindingCreate(BindingBase):
    collection_name: Optional[str] = None
    collection_id: Optional[str] = None
    transformer_name: Optional[str] = None
    transformer_id: Optional[str] = None
    index_name: Optional[str] = None
    index_id: Optional[str] = None

    # Ensure either `_name` or `_id` is provided for collection, transformer, and index
    @model_validator(mode="before")
    def check_identifiers(cls, values):
        if not values.get("collection_name") and not values.get("collection_id"):
            raise ValueError("Either collection_name or collection_id must be provided")
        if not values.get("transformer_name") and not values.get("transformer_id"):
            raise ValueError(
                "Either transformer_name or transformer_id must be provided"
            )
        if not values.get("index_name") and not values.get("index_id"):
            raise ValueError("Either index_name or index_id must be provided")
        return values


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
