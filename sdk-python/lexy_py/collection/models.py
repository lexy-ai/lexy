from datetime import datetime
from typing import Any, Optional, TYPE_CHECKING

from PIL import Image
from pydantic import BaseModel, Field, PrivateAttr

from lexy_py.document.models import Document

if TYPE_CHECKING:
    from lexy_py.client import LexyClient


class CollectionModel(BaseModel):
    """ Collection model """
    collection_name: str = Field(
        title="Collection Name",
        description="The name of the collection. Must be unique across collections.",
        min_length=1,
        max_length=56,
        pattern="^[a-z_][a-z0-9_]{0,55}$",
    )
    description: Optional[str] = None
    config: Optional[dict[str, Any]] = Field(default={})
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    collection_id: Optional[str] = None

    def __repr__(self):
        return f"<Collection('{self.collection_name}', id='{self.collection_id}', description='{self.description}')>"


class CollectionUpdate(BaseModel):
    """ Collection update model """
    collection_name: Optional[str] = Field(
        default=None,
        title="Collection Name",
        description="The name of the collection. Must be unique across collections.",
        min_length=1,
        max_length=56,
        pattern="^[a-z_][a-z0-9_]{0,55}$",
    )
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

    def add_documents(self,
                      docs: Document | dict | list[Document | dict],
                      *,
                      batch_size: int = 100) -> list[Document]:
        """ Synchronously add documents to the collection in batches.

        Args:
            docs (Document | dict | list[Document | dict]): The documents to add.
            batch_size (int): The number of documents to add in each batch. Defaults to 100.

        Returns:
            Documents: A list of created documents.
        """
        return self.client.document.add_documents(docs, collection_id=self.collection_id, batch_size=batch_size)

    # TODO: add pagination
    def list_documents(self, *, limit: int = 100, offset: int = 0) -> list[Document]:
        """ Synchronously get a list of documents in the collection.

        Args:
            limit (int): The maximum number of documents to return. Defaults to 100. Maximum allowed is 1000.
            offset (int): The offset to start from. Defaults to 0.

        Returns:
            Documents: A list of documents in the collection.
        """
        return self.client.document.list_documents(collection_id=self.collection_id, limit=limit, offset=offset)

    def upload_documents(self,
                         files: str | Image.Image | list[str | Image.Image],
                         filenames: str | list[str] = None,
                         *,
                         batch_size: int = 5) -> list[Document]:
        """ Synchronously upload files to the collection in batches.

        Args:
            files (str | Image.Image | list[str | Image.Image]): The files to upload. Can be a single instance or a
                list of a string containing the path to a file or an `Image.Image` object.
            filenames (str | list[str], optional): The filenames of the files to upload. Defaults to None.
            batch_size (int): The number of files to upload in each batch. Defaults to 5.

        Returns:
            Documents: A list of created documents.

        Raises:
            TypeError: If an input file type is invalid.
            ValueError: If the length of the filenames list does not match the length of the files list.

        Examples:
            >>> from lexy_py import LexyClient
            >>> lx = LexyClient()
            >>> collection = lx.create_collection(collection_name='my_file_collection')
            >>> collection.upload_documents(
            ...     files=[
            ...         'lexy/sample_data/images/lexy-dalle.jpeg',
            ...         'lexy/sample_data/images/lexy.png',
            ...         'dais2023-233180.pdf',
            ...         'gwdemo30.mp4',
            ...         'kindle2.html',
            ...     ]
            ... )
        """
        return self.client.document.upload_documents(files=files,
                                                     filenames=filenames,
                                                     collection_id=self.collection_id,
                                                     batch_size=batch_size)
