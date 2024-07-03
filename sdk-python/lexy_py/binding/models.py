from datetime import datetime
from enum import Enum
from typing import Any, Optional, TYPE_CHECKING

from pydantic import BaseModel, Field, PrivateAttr, field_validator, model_validator

from lexy_py.collection.models import CollectionModel, Collection
from lexy_py.index.models import IndexModel, Index
from lexy_py.transformer.models import TransformerModel, Transformer
from lexy_py.filters import FilterBuilder

if TYPE_CHECKING:
    from lexy_py.client import LexyClient


class BindingStatus(str, Enum):
    PENDING = "pending"
    ON = "on"
    OFF = "off"
    DETACHED = "detached"


# Shared properties
class BindingBase(BaseModel):
    """Binding base model"""

    description: Optional[str] = None
    execution_params: Optional[dict[str, Any]] = Field(default={})
    transformer_params: Optional[dict[str, Any]] = Field(default={})
    filter: Optional[dict[str, Any]] = None
    status: Optional[BindingStatus] = Field(default=BindingStatus.PENDING)

    # If a FilterBuilder instance is provided for `filter`, convert it to a dict
    @field_validator("filter", mode="before")
    @classmethod
    def filter_to_dict(cls, value: Optional[FilterBuilder | dict]) -> Optional[dict]:
        if isinstance(value, FilterBuilder):
            return value.to_dict()
        return value


class BindingModel(BindingBase):
    """Binding model"""

    binding_id: int
    collection_id: str
    transformer_id: str
    index_id: str
    collection: CollectionModel
    transformer: TransformerModel
    index: IndexModel
    created_at: datetime
    updated_at: datetime

    def __repr__(self):
        return (
            f"<Binding("
            f"id={self.binding_id}, "
            f"status={self.status.name}, "
            f"collection='{self.collection_id}', "
            f"transformer='{self.transformer_id}', "
            f"index='{self.index_id}')>"
        )


class BindingCreate(BindingBase):
    """Binding create model"""

    collection_name: Optional[str] = None
    collection_id: Optional[str] = None
    transformer_name: Optional[str] = None
    transformer_id: Optional[str] = None
    index_name: Optional[str] = None
    index_id: Optional[str] = None

    # Ensure either `_name` or `_id` is provided for collection, transformer, and index
    @model_validator(mode="before")
    def check_identifiers(cls, values):
        if not values.get("collection_name") and not values.get("collection_id"):
            raise ValueError("Either collection_name or collection_id must be provided")
        if not values.get("transformer_name") and not values.get("transformer_id"):
            raise ValueError(
                "Either transformer_name or transformer_id must be provided"
            )
        if not values.get("index_name") and not values.get("index_id"):
            raise ValueError("Either index_name or index_id must be provided")
        return values


class BindingUpdate(BindingBase):
    """Binding update model"""

    description: Optional[str] = None
    execution_params: Optional[dict[str, Any]] = None
    transformer_params: Optional[dict[str, Any]] = None
    filter: Optional[dict[str, Any]] = None
    status: Optional[BindingStatus] = None


class Binding(BindingModel):
    __doc__ = BindingModel.__doc__
    _client: Optional["LexyClient"] = PrivateAttr(default=None)

    def __init__(self, **data: Any):
        super().__init__(**data)
        self._client = data.pop("client", None)
        self.collection: Collection = Collection(
            **self.collection.model_dump(), client=self._client
        )
        self.index: Index = Index(**self.index.model_dump(), client=self._client)
        self.transformer: Transformer = Transformer(
            **self.transformer.model_dump(), client=self._client
        )

    @property
    def client(self) -> "LexyClient":
        if not self._client:
            raise ValueError("API client has not been set.")
        return self._client
