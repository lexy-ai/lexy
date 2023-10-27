from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

from lexy_py.collection.models import Collection
from lexy_py.index.models import Index
from lexy_py.transformer.models import Transformer


class BindingStatus(str, Enum):
    PENDING = "pending"
    ON = "on"
    OFF = "off"
    DETACHED = "detached"


class TransformerIndexBinding(BaseModel):
    """ Transformer-index binding model """

    binding_id: Optional[int] = None
    collection_id: Optional[str] = None
    transformer_id: Optional[str] = None
    index_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    description: Optional[str] = None
    execution_params: Optional[dict[str, Any]] = Field(default={})
    transformer_params: Optional[dict[str, Any]] = Field(default={})
    filters: Optional[dict] = Field(default={})
    status: Optional[BindingStatus] = Field(default=BindingStatus.PENDING)

    collection: Optional[Collection] = None
    transformer: Optional[Transformer] = None
    index: Optional[Index] = None

    def __repr__(self):
        return f"<TransformerIndexBinding " \
               f"id={self.binding_id}, " \
               f"status={self.status.name}, " \
               f"collection_id={self.collection_id}, " \
               f"transformer_id={self.transformer_id}, " \
               f"index_id={self.index_id}>"


class TransformerIndexBindingUpdate(BaseModel):
    """ Transformer-index binding update model """

    description: Optional[str] = None
    execution_params: Optional[dict[str, Any]] = None
    transformer_params: Optional[dict[str, Any]] = None
    filters: Optional[dict[str, Any]] = None
    status: Optional[BindingStatus] = None
