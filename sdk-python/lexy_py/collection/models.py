from datetime import datetime
from typing import Any, Optional, TYPE_CHECKING

from pydantic import BaseModel, Field, PrivateAttr

from lexy_py.document.models import Document

if TYPE_CHECKING:
    from lexy_py.client import LexyClient


class CollectionModel(BaseModel):
    """ Collection model """
    collection_id: str = Field(
        min_length=1,
        max_length=255,
        regex=r"^[a-z0-9_-]+$"
    )
    description: Optional[str] = None
    config: Optional[dict[str, Any]] = Field(default={})
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __repr__(self):
        return f"<Collection('{self.collection_id}', description='{self.description}')>"


class CollectionUpdate(BaseModel):
    """ Collection update model """
    description: Optional[str] = None
    config: Optional[dict[str, Any]] = None


class Collection(CollectionModel):
    __doc__ = CollectionModel.__doc__
    _client: Optional["LexyClient"] = PrivateAttr(default=None)

    def __init__(self, **data: Any):
        super().__init__(**data)
        self._client = data.pop('client', None)

    @property
    def client(self) -> "LexyClient":
        if not self._client:
            raise ValueError("API client has not been set.")
        return self._client

    def add_documents(self, docs: Document | dict | list[Document | dict]) -> list[Document]:
        """ Synchronously add documents to the collection.

        Args:
            docs (Document | dict | list[Document | dict]): The documents to add.

        Returns:
            Documents: A list of added documents.
        """
        return self.client.document.add_documents(docs, collection_id=self.collection_id)

    # TODO: add pagination
    def list_documents(self, limit: int = 100, offset: int = 0) -> list[Document]:
        """ Synchronously get a list of documents in the collection.

        Args:
            limit (int): The maximum number of documents to return. Defaults to 100. Maximum allowed is 1000.
            offset (int): The offset to start from. Defaults to 0.

        Returns:
            Documents: A list of documents in the collection.
        """
        return self.client.document.list_documents(self.collection_id, limit=limit, offset=offset)
