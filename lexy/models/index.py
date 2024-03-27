from datetime import datetime
from typing import Any, Optional, TYPE_CHECKING

from sqlalchemy import Column, DateTime, JSON, func, String
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from lexy.models.binding import Binding


def default_index_table_name(context) -> str:
    index_id = context.get_current_parameters()["index_id"]
    return f"zzidx__{index_id}"


class IndexBase(SQLModel):
    index_id: str = Field(
        default=None,
        primary_key=True,
        min_length=1,
        max_length=56,
        # Postgres identifiers are limited to 63 characters (so 63 - len('zzidx__') = 56)
        # TODO: switch back to `regex=` (or `pattern=`) once SQLModel bug is fixed
        #   https://github.com/tiangolo/sqlmodel/discussions/735
        schema_extra={"pattern": r"^[a-z_][a-z0-9_]{0,55}$"}
    )
    description: Optional[str] = None
    index_table_schema: Optional[dict[str, Any]] = Field(sa_column=Column(JSON, nullable=False), default={})
    index_fields: Optional[dict[str, Any]] = Field(sa_column=Column(JSON, nullable=False), default={})


class Index(IndexBase, table=True):
    __tablename__ = "indexes"
    created_at: datetime = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )
    updated_at: datetime = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()),
    )
    bindings: list["Binding"] = Relationship(
        back_populates="index",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    index_table_name: str = Field(
        default=None,
        # Postgres identifiers are limited to 63 characters
        # TODO: switch back to `regex=` (or `pattern=`) once SQLModel bug is fixed
        #   https://github.com/tiangolo/sqlmodel/discussions/735
        schema_extra={"pattern": r"^[a-z_][a-z0-9_]{0,62}$"},
        sa_column=Column(String, default=default_index_table_name, nullable=False, unique=True),
    )


class IndexCreate(IndexBase):
    pass


class IndexUpdate(IndexBase):
    description: Optional[str] = None
    index_table_schema: Optional[dict[str, Any]] = None
    index_fields: Optional[dict[str, Any]] = None
