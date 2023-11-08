from datetime import datetime
from enum import Enum
from typing import Any, Optional, TYPE_CHECKING

from pydantic import BaseModel, Field, PrivateAttr

from lexy_py.collection.models import CollectionModel, Collection
from lexy_py.index.models import IndexModel, Index
from lexy_py.transformer.models import TransformerModel, Transformer

if TYPE_CHECKING:
    from lexy_py.client import LexyClient


class BindingStatus(str, Enum):
    PENDING = "pending"
    ON = "on"
    OFF = "off"
    DETACHED = "detached"


class TransformerIndexBindingModel(BaseModel):
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

    collection: Optional[CollectionModel] = None
    transformer: Optional[TransformerModel] = None
    index: Optional[IndexModel] = None

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


class TransformerIndexBinding(TransformerIndexBindingModel):
    __doc__ = TransformerIndexBindingModel.__doc__
    _client: Optional["LexyClient"] = PrivateAttr(default=None)

    def __init__(self, **data: Any):
        super().__init__(**data)
        self._client = data.pop('client', None)
        self.collection: Collection = Collection(**self.collection.dict(), client=self._client)
        self.index: Index = Index(**self.index.dict(), client=self._client)
        self.transformer: Transformer = Transformer(**self.transformer.dict(), client=self._client)

    @property
    def client(self) -> "LexyClient":
        if not self._client:
            raise ValueError("API client has not been set.")
        return self._client
