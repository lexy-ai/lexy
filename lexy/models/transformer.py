from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Column, DateTime, func, String
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from sqlalchemy.engine.default import DefaultExecutionContext
    from lexy.models.binding import Binding


def default_celery_task_name(transformer_id: str) -> str:
    return f"lexy.transformers.{transformer_id}"


def sa_default_celery_task_name(context: "DefaultExecutionContext") -> str:
    transformer_id = context.get_current_parameters()["transformer_id"]
    return default_celery_task_name(transformer_id)


class TransformerBase(SQLModel):
    transformer_id: str = Field(
        default=None,
        primary_key=True,
        min_length=1,
        max_length=255,
        # TODO: switch back to `regex=` (or `pattern=`) once SQLModel bug is fixed
        #   https://github.com/tiangolo/sqlmodel/discussions/735
        schema_extra={"pattern": r"^[a-zA-Z][a-zA-Z0-9_.-]+$"},
    )
    path: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
        # TODO: switch back to `regex=` (or `pattern=`) once SQLModel bug is fixed
        #   https://github.com/tiangolo/sqlmodel/discussions/735
        schema_extra={"pattern": r"^[a-zA-Z][a-zA-Z0-9_.]+$"},
    )
    description: Optional[str] = None


class Transformer(TransformerBase, table=True):
    __tablename__ = "transformers"
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
    bindings: list["Binding"] = Relationship(back_populates="transformer")
    celery_task_name: Optional[str] = Field(
        default=None,
        sa_column=Column(
            String,
            default=sa_default_celery_task_name,
            nullable=True,
            unique=True,
        ),
    )


class TransformerCreate(TransformerBase):
    pass


class TransformerUpdate(TransformerBase):
    description: Optional[str] = None
    path: Optional[str] = None
