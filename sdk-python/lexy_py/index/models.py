from datetime import datetime
from typing import Any, Optional, TYPE_CHECKING

from pydantic import BaseModel, Field, PrivateAttr

if TYPE_CHECKING:
    from lexy_py.client import LexyClient


class IndexModel(BaseModel):
    """ Index model """
    index_id: str = Field(..., min_length=1, description="The ID of the index.")
    description: Optional[str] = None
    index_table_schema: Optional[dict[str, Any]] = Field(default={})
    index_fields: Optional[dict[str, Any]] = Field(default={})
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    index_table_name: Optional[str] = None

    def __repr__(self):
        return f"<Index('{self.index_id}', description='{self.description}')>"


class IndexUpdate(BaseModel):
    """ Index update model """
    description: Optional[str] = None
    index_table_schema: Optional[dict[str, Any]] = None
    index_fields: Optional[dict[str, Any]] = None


class Index(IndexModel):
    __doc__ = IndexModel.__doc__
    _client: Optional["LexyClient"] = PrivateAttr(default=None)

    def __init__(self, **data: Any):
        super().__init__(**data)
        self._client = data.pop('client', None)

    @property
    def client(self) -> "LexyClient":
        if not self._client:
            raise ValueError("API client has not been set.")
        return self._client

    def query(self, query_string: str, query_field: str = "embedding", k: int = 5) -> list[dict]:
        """ Synchronously query an index.

        Args:
            query_string (str): The query string.
            query_field (str, optional): The field to query. Defaults to "embedding".
            k (int, optional): The number of records to return. Defaults to 5.

        Returns:
            list[dict]: The query results.
        """
        return self.client.index.query_index(query_string, self.index_id, query_field, k)
