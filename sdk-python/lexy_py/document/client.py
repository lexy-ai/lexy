""" Client for interacting with the Document API. """

import io
import json
import mimetypes
import os
from typing import Optional, TYPE_CHECKING

import httpx
from PIL import Image

from lexy_py.exceptions import handle_response
from .models import Document, DocumentUpdate

if TYPE_CHECKING:
    from lexy_py.client import LexyClient


class DocumentClient:
    """
    This class is used to interact with the Lexy Document API.

    Properties:
        aclient (httpx.AsyncClient): Asynchronous API client.
        client (httpx.Client): Synchronous API client.
    """

    def __init__(self, lexy_client: "LexyClient") -> None:
        self._lexy_client = lexy_client

    @property
    def aclient(self) -> httpx.AsyncClient:
        return self._lexy_client.aclient

    @property
    def client(self) -> httpx.Client:
        return self._lexy_client.client

    def list_documents(self,
                       collection_id: str = "default",
                       limit: int = 100,
                       offset: int = 0) -> list[Document]:
        """ Synchronously get a list of documents in a collection.

        Args:
            collection_id (str): The ID of the collection to get documents from. Defaults to "default".
            limit (int): The maximum number of documents to return. Defaults to 100. Maximum allowed is 1000.
            offset (int): The offset to start from. Defaults to 0.

        Returns:
            Documents: A list of documents in a collection.
        """
        r = self.client.get("/documents",
                            params={
                                "collection_id": collection_id,
                                "limit": limit,
                                "offset": offset
                            })
        handle_response(r)
        return [Document(**document, client=self._lexy_client) for document in r.json()]

    async def alist_documents(self,
                              collection_id: str = "default",
                              limit: int = 100,
                              offset: int = 0) -> list[Document]:
        """ Asynchronously get a list of documents in a collection.

        Args:
            collection_id (str): The ID of the collection to get documents from. Defaults to "default".
            limit (int): The maximum number of documents to return. Defaults to 100. Maximum allowed is 1000.
            offset (int): The offset to start from. Defaults to 0.

        Returns:
            Documents: A list of documents in a collection.
        """
        r = await self.aclient.get("/documents",
                                   params={
                                       "collection_id": collection_id,
                                       "limit": limit,
                                       "offset": offset
                                   })
        handle_response(r)
        return [Document(**document, client=self._lexy_client) for document in r.json()]

    def add_documents(self,
                      docs: Document | dict | list[Document | dict],
                      collection_id: str = "default",
                      batch_size: int = 100) -> list[Document]:
        """ Synchronously add documents to a collection in batches.

        Args:
            docs (Document | dict | list[Document | dict]): The documents to add.
            collection_id (str): The ID of the collection to add the documents to. Defaults to "default".
            batch_size (int): The number of documents to add in each batch. Defaults to 100.

        Returns:
            Documents: A list of created documents.

        Examples:
            >>> from lexy_py import LexyClient
            >>> lexy = LexyClient()
            >>> docs_added = lexy.add_documents(docs=[
            ...     {"content": "My first document"},
            ...     {"content": "My second document"}
            ... ], collection_id="my_collection")
        """
        created_docs = []
        processed_docs = self._process_docs(docs)

        for i in range(0, len(processed_docs), batch_size):
            batch_docs = processed_docs[i:i + batch_size]
            r = self.client.post("/documents", json=batch_docs, params={"collection_id": collection_id})
            handle_response(r)
            created_docs.extend([Document(**document['document'], client=self._lexy_client) for document in r.json()])
        return created_docs

    async def aadd_documents(self,
                             docs: Document | dict | list[Document | dict],
                             collection_id: str = "default",
                             batch_size: int = 100) -> list[Document]:
        """ Asynchronously add documents to a collection in batches.

        Args:
            docs (Document | dict | list[Document | dict]): The documents to add.
            collection_id (str): The ID of the collection to add the documents to. Defaults to "default".
            batch_size (int): The number of documents to add in each batch. Defaults to 100.

        Returns:
            Documents: A list of created documents.
        """
        created_docs = []
        processed_docs = self._process_docs(docs)

        for i in range(0, len(processed_docs), batch_size):
            batch_docs = processed_docs[i:i + batch_size]
            r = await self.aclient.post("/documents", json=batch_docs, params={"collection_id": collection_id})
            handle_response(r)
            created_docs.extend([Document(**document['document'], client=self._lexy_client) for document in r.json()])
        return created_docs

    def add_document(self, doc: Document | dict, collection_id: str) -> Document:
        """ Synchronously add a document to a collection.

        Args:
            doc (Document | dict): The document to add.
            collection_id (str): The ID of the collection to add the document to.

        Returns:
            Document: The created document.
        """
        processed_docs = self._process_docs(doc)

        r = self.client.post("/documents", json=processed_docs, params={"collection_id": collection_id})
        handle_response(r)
        return Document(**r.json()[0]['document'], client=self._lexy_client)

    async def aadd_document(self, doc: Document | dict, collection_id: str) -> Document:
        """ Asynchronously add a document to a collection.

        Args:
            doc (Document | dict): The document to add.
            collection_id (str): The ID of the collection to add the document to.

        Returns:
            Document: The created document.
        """
        processed_docs = self._process_docs(doc)

        r = await self.aclient.post("/documents", json=processed_docs, params={"collection_id": collection_id})
        handle_response(r)
        return Document(**r.json()[0]['document'], client=self._lexy_client)

    def get_document(self, document_id: str) -> Document:
        """ Synchronously get a document.

        Args:
            document_id (str): The ID of the document to get.

        Returns:
            Document: The document.
        """
        r = self.client.get(f"/documents/{document_id}")
        handle_response(r)
        return Document(**r.json(), client=self._lexy_client)

    async def aget_document(self, document_id: str) -> Document:
        """ Asynchronously get a document.

        Args:
            document_id (str): The ID of the document to get.

        Returns:
            Document: The document.
        """
        r = await self.aclient.get(f"/documents/{document_id}")
        handle_response(r)
        return Document(**r.json(), client=self._lexy_client)

    def update_document(self, document_id: str, content: Optional[str] = None, meta: Optional[dict] = None) -> Document:
        """ Synchronously update a document.

        Args:
            document_id (str): The ID of the document to update.
            content (str, optional): The new content of the document.
            meta (dict, optional): The new metadata for the document.

        Returns:
            Document: The updated document.
        """
        document = DocumentUpdate(content=content, meta=meta)
        r = self.client.patch(f"/documents/{document_id}", json=document.dict(exclude_none=True))
        handle_response(r)
        return Document(**r.json()['document'], client=self._lexy_client)

    async def aupdate_document(self, document_id: str, content: Optional[str] = None,
                               meta: Optional[dict] = None) -> Document:
        """ Asynchronously update a document.

        Args:
            document_id (str): The ID of the document to update.
            content (str, optional): The new content of the document.
            meta (dict, optional): The new metadata for the document.

        Returns:
            Document: The updated document.
        """
        document = DocumentUpdate(content=content, meta=meta)
        r = await self.aclient.patch(f"/documents/{document_id}", json=document.dict(exclude_none=True))
        handle_response(r)
        return Document(**r.json()['document'], client=self._lexy_client)

    def delete_document(self, document_id: str) -> dict:
        """ Synchronously delete a document.

        Args:
            document_id (str): The ID of the document to delete.
        """
        r = self.client.delete(f"/documents/{document_id}")
        handle_response(r)
        return r.json()

    async def adelete_document(self, document_id: str) -> dict:
        """ Asynchronously delete a document.

        Args:
            document_id (str): The ID of the document to delete.
        """
        r = await self.aclient.delete(f"/documents/{document_id}")
        handle_response(r)
        return r.json()

    def bulk_delete_documents(self, collection_id: str) -> dict:
        """ Synchronously delete all documents from a collection.

        Args:
            collection_id (str): The ID of the collection to delete documents from.
        """
        r = self.client.delete("/documents", params={"collection_id": collection_id})
        handle_response(r)
        return r.json()

    def upload_documents(self,
                         files: Image.Image | str | list[Image.Image | str],
                         filenames: str | list[str] = None,
                         collection_id: str = "default",
                         batch_size: int = 5) -> list[Document]:
        """ Synchronously upload files to a collection in batches.

        Args:
            files (Image.Image | str | list[Image.Image | str]): The files to upload. Can be a list or single instance
                of either an Image file or a string containing the path to an Image file.
            filenames (str | list[str], optional): The filenames of the files to upload. Defaults to None.
            collection_id (str): The ID of the collection to upload the files to. Defaults to "default".
            batch_size (int): The number of files to upload in each batch. Defaults to 5.

        Returns:
            Documents: A list of created documents.
        """
        created_docs = []
        files, filenames = self._align_filenames(files, filenames)

        # process and upload files in batches
        for i in range(0, len(files), batch_size):
            batch_files = files[i:i + batch_size]
            batch_filenames = filenames[i:i + batch_size]
            processed_images = self._process_images(batch_files, filenames=batch_filenames)
            r = self.client.post("/documents/upload",
                                 files=processed_images,
                                 params={"collection_id": collection_id})
            handle_response(r)
            created_docs.extend([Document(**document['document'], client=self._lexy_client) for document in r.json()])
        return created_docs

    async def aupload_documents(self,
                                files: Image.Image | str | list[Image.Image | str],
                                filenames: str | list[str] = None,
                                collection_id: str = "default",
                                batch_size: int = 5) -> list[Document]:
        """ Asynchronously upload files to a collection in batches.

        Args:
            files (Image.Image | str | list[Image.Image | str]): The files to upload. Can be a list or single instance
                of either an Image file or a string containing the path to an Image file.
            filenames (str | list[str], optional): The filenames of the files to upload. Defaults to None.
            collection_id (str): The ID of the collection to upload the files to. Defaults to "default".
            batch_size (int): The number of files to upload in each batch. Defaults to 5.

        Returns:
            Documents: A list of created documents.
        """
        created_docs = []
        files, filenames = self._align_filenames(files, filenames)

        # process and upload files in batches
        for i in range(0, len(files), batch_size):
            batch_files = files[i:i + batch_size]
            batch_filenames = filenames[i:i + batch_size]
            processed_images = self._process_images(batch_files, filenames=batch_filenames)
            r = await self.aclient.post("/documents/upload",
                                        files=processed_images,
                                        params={"collection_id": collection_id})
            handle_response(r)
            created_docs.extend([Document(**document['document'], client=self._lexy_client) for document in r.json()])
        return created_docs

    def get_document_urls(self, document_id: str, expiration: int = 3600) -> dict:
        """ Synchronously get presigned URLs for a document.

        Args:
            document_id (str): The ID of the document to get presigned URL for.
            expiration (int): The expiration time of the presigned URLs in seconds. Defaults to 3600.

        Returns:
            dict: A dictionary containing presigned URLs.

        Examples:
            >>> from lexy_py import LexyClient
            >>> lexy = LexyClient()
            >>> my_image_document = lexy.list_documents('my-image-collection', limit=1)[0]
            >>> lexy.document.get_document_urls(document_id=my_image_document.document_id)
            {
                "object": "https://my-bucket.s3.amazonaws.com/path/to/object?...",
                "thumbnails": {
                    "256x256": "https://my-bucket.s3.amazonaws.com/path/to/thumbnail?..."
                }
            }

            >>> my_pdf_document = lexy.list_documents('pdf-collection', limit=1)[0]
            >>> lexy.document.get_document_urls(document_id=my_pdf_document.document_id)
            {
                "object": "https://my-bucket.s3.amazonaws.com/path/to/object?...",
            }
        """
        r = self.client.get(f"/documents/{document_id}/urls", params={"expiration": expiration})
        handle_response(r)
        return r.json()

    async def aget_document_urls(self, document_id: str, expiration: int = 3600) -> dict:
        """ Asynchronously get presigned URLs for a document.

        Args:
            document_id (str): The ID of the document to get presigned URL for.
            expiration (int): The expiration time of the presigned URLs in seconds. Defaults to 3600.

        Returns:
            dict: A dictionary containing presigned URLs.
        """
        r = await self.aclient.get(f"/documents/{document_id}/urls", params={"expiration": expiration})
        handle_response(r)
        return r.json()

    @staticmethod
    def _align_filenames(files, filenames: str | list[str] = None) -> tuple[list, list]:
        """ Align files and filenames. """
        # ensure files is a list
        if not isinstance(files, list):
            files = [files]

        # if filenames is a single string (or None), convert it to a list with repeated elements
        if isinstance(filenames, str) or filenames is None:
            filenames = [filenames] * len(files)

        if len(files) != len(filenames):
            raise ValueError("Length of filenames list must match length of files list")
        return files, filenames

    @staticmethod
    def _process_docs(docs: Document | dict | list[Document | dict]) -> list[dict]:
        """ Process documents into a list of json-serializable dictionaries. """
        processed_docs = []

        if isinstance(docs, (Document, dict)):
            docs = [docs]

        for doc in docs:
            if isinstance(doc, Document):
                # TODO: use doc.model_dump(mode='json') after updating to Pydantic 2.0
                processed_docs.append(json.loads(doc.json()))
            elif isinstance(doc, dict):
                doc = Document(**doc)
                # TODO: use doc.model_dump(mode='json') after updating to Pydantic 2.0
                processed_docs.append(json.loads(doc.json()))
            else:
                raise TypeError(f"Invalid type for doc item: {type(doc)} - must be Document or dict")

        return processed_docs

    @staticmethod
    def _process_images(images: Image.Image | str | list[Image.Image | str],
                        filenames: str | list[str] = None) -> list:

        processed_images = []
        images, filenames = DocumentClient._align_filenames(images, filenames)

        for img, filename in zip(images, filenames):
            if isinstance(img, str):
                image = Image.open(img)
                if not filename:
                    filename = os.path.basename(img)
            elif isinstance(img, Image.Image):
                image = img
                if not filename:
                    filename = f'image.{image.format.lower()}' if image.format else 'image.jpg'
            else:
                raise TypeError(f"Invalid type for image: {type(img)} - must be Image.Image or str")

            buffer = io.BytesIO()
            image_format = image.format or "jpg"
            image.save(buffer, format=image_format)
            buffer.seek(0)
            mime_type = mimetypes.types_map.get(f".{image_format.lower()}", "application/octet-stream")
            processed_images.append(('files', (filename, buffer, mime_type)))

        return processed_images
