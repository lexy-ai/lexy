from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Transformer(BaseModel):
    """ Transformer model """

    transformer_id: str = Field(..., min_length=1, max_length=255, regex=r"^[a-zA-Z][a-zA-Z0-9_.]+$")
    path: Optional[str] = Field(..., min_length=1, max_length=255, regex=r"^[a-zA-Z][a-zA-Z0-9_.]+$")
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class TransformerUpdate(BaseModel):
    path: Optional[str] = None
    description: Optional[str] = None
