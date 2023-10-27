from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Collection(BaseModel):
    """ Collection model """

    collection_id: str = Field(
        min_length=1,
        max_length=255,
        regex=r"^[a-z0-9_-]+$"
    )
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
