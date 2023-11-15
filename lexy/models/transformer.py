from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Column, DateTime, func
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from lexy.models.binding import Binding


class TransformerBase(SQLModel):
    transformer_id: str = Field(
        default=None,
        primary_key=True,
        min_length=1,
        max_length=255,
        regex=r"^[a-zA-Z][a-zA-Z0-9_.]+$"
    )
    path: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
        regex=r"^[a-zA-Z][a-zA-Z0-9_.]+$"
    )
    description: Optional[str] = None


class Transformer(TransformerBase, table=True):
    __tablename__ = "transformers"
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()),
    )
    bindings: list["Binding"] = Relationship(back_populates="transformer")


class TransformerCreate(TransformerBase):
    pass


class TransformerUpdate(TransformerBase):
    description: Optional[str] = None
    path: Optional[str] = None
