from datetime import datetime
from typing import Any, Optional, TYPE_CHECKING

from PIL import Image
from pydantic import BaseModel, Field, PrivateAttr

if TYPE_CHECKING:
    from lexy_py.client import LexyClient


class IndexModel(BaseModel):
    """ Index model """
    index_id: str = Field(
        default=...,
        min_length=1,
        max_length=56,
        pattern="^[a-z_][a-z0-9_]{0,55}$",
        description="The ID of the index."
    )
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

    def query(self,
              query_text: str = None,
              query_image: Image.Image | str = None,
              query_field: str = "embedding",
              k: int = 5,
              return_fields: list[str] = None,
              return_document: bool = False,
              embedding_model: str = None) -> list[dict]:
        """ Synchronously query an index.

        Args:
            query_text (str): The query text.
            query_image (Image.Image | str): The query image. Can be a PIL Image object or a path to an image.
            query_field (str, optional): The field to query. Defaults to "embedding".
            k (int, optional): The number of records to return. Defaults to 5.
            return_fields (list[str], optional): The fields to return. Defaults to None, which returns all fields. To
                return fields from the linked document, use "document.<field_name>".
            return_document (bool, optional): Whether to return the document object. Defaults to False.
            embedding_model (str, optional): The name of the embedding model to use. Defaults to None, which uses the
                embedding model associated with `index_id.query_field`.

        Returns:
            Results: A list of query results.
        """
        return self.client.index.query_index(query_text=query_text,
                                             query_image=query_image,
                                             index_id=self.index_id,
                                             query_field=query_field,
                                             k=k,
                                             return_fields=return_fields,
                                             return_document=return_document,
                                             embedding_model=embedding_model)

    def list_records(self, document_id: Optional[str] = None) -> list[dict]:
        """ Synchronously list all records in the index.

        Args:
            document_id (str, optional): The document ID to filter by. Defaults to None.

        Returns:
            list[dict]: A list of records.
        """
        return self.client.index.list_index_records(self.index_id, document_id=document_id)
