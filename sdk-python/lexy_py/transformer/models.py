from datetime import datetime
from typing import Any, Optional, TYPE_CHECKING

from pydantic import BaseModel, Field, PrivateAttr

if TYPE_CHECKING:
    from lexy_py.client import LexyClient


class TransformerModel(BaseModel):
    """ Transformer model """
    transformer_id: str = Field(..., min_length=1, max_length=255, regex=r"^[a-zA-Z][a-zA-Z0-9_.]+$")
    path: Optional[str] = Field(..., min_length=1, max_length=255, regex=r"^[a-zA-Z][a-zA-Z0-9_.]+$")
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __repr__(self):
        return f"<Transformer('{self.transformer_id}', description='{self.description}')>"


class TransformerUpdate(BaseModel):
    """ Transformer update model """
    path: Optional[str] = None
    description: Optional[str] = None


class Transformer(TransformerModel):
    __doc__ = TransformerModel.__doc__
    _client: Optional["LexyClient"] = PrivateAttr(default=None)

    def __init__(self, **data: Any):
        super().__init__(**data)
        self._client = data.pop('client', None)

    @property
    def client(self) -> "LexyClient":
        if not self._client:
            raise ValueError("API client has not been set.")
        return self._client
