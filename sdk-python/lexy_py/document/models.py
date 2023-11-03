from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class Document(BaseModel):
    """ Document model """

    document_id: Optional[str] = None
    content: str = Field(..., min_length=1)
    meta: Optional[dict[Any, Any]] = Field(default={})
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    collection_id: Optional[str] = None


class DocumentCreate(BaseModel):
    """ Document create model """

    content: str = Field(..., min_length=1)
    meta: Optional[dict[Any, Any]] = Field(default={})


class DocumentUpdate(BaseModel):
    """ Document update model """

    content: Optional[str] = None
    meta: Optional[dict[Any, Any]] = None
