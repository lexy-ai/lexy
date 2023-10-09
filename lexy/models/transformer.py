from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, func
from sqlmodel import SQLModel, Field, Relationship


class TransformerBase(SQLModel):
    transformer_id: str = Field(
        default=None,
        primary_key=True,
        min_length=1,
        max_length=255,
        regex=r"^[a-zA-Z][a-zA-Z0-9_.]+$"
    )
    code: str = Field(
        default=None,
        min_length=1,
        max_length=255*255,
    )
    description: Optional[str] = None


class Transformer(TransformerBase, table=True):
    __tablename__ = "transformers"
    created_at: datetime = Field(
        nullable=False,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    updated_at: datetime = Field(
        nullable=False,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now()),
    )
    index_bindings: list["TransformerIndexBinding"] = Relationship(back_populates="transformer")


class TransformerCreate(TransformerBase):
    pass


class TransformerUpdate(TransformerBase):
    description: Optional[str] = None
