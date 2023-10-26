from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class Index(BaseModel):
    """ Index model """

    index_id: str = Field(..., min_length=1)
    description: Optional[str] = None
    index_table_schema: Optional[dict[str, Any]] = Field(default={})
    index_fields: Optional[dict[str, Any]] = Field(default={})
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    index_table_name: Optional[str] = None


class IndexUpdate(BaseModel):
    """ Index update model """

    description: Optional[str] = None
    index_table_schema: Optional[dict[str, Any]] = None
    index_fields: Optional[dict[str, Any]] = None
