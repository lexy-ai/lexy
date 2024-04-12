""" Client for interacting with the Document API. """

import mimetypes
import os
from io import BytesIO
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

    Attributes:
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
                       *,
                       collection_name: str | None = "default",
                       collection_id: str = None,
                       limit: int = 100,
                       offset: int = 0) -> list[Document]:
        """ Synchronously get a list of documents in a collection.

        If both `collection_name` and `collection_id` are provided, `collection_id` will be used.

        Args:
            collection_name (str): The name of the collection to get documents from. Defaults to "default".
            collection_id (str): The ID of the collection to get documents from. Defaults to None. If provided,
                `collection_name` will be ignored.
            limit (int): The maximum number of documents to return. Defaults to 100. Maximum allowed is 1000.
            offset (int): The offset to start from. Defaults to 0.

        Returns:
            Documents: A list of documents in a collection.
        """
        if collection_id is not None:
            r = self.client.get(f"/collections/{collection_id}/documents",
                                params={"limit": limit, "offset": offset})
        else:
            r = self.client.get("/documents",
                                params={
                                    "collection_name": collection_name,
                                    "limit": limit,
                                    "offset": offset
                                })
        handle_response(r)
        return [Document(**document, client=self._lexy_client) for document in r.json()]

    async def alist_documents(self,
                              *,
                              collection_name: str = "default",
                              collection_id: str = None,
                              limit: int = 100,
                              offset: int = 0) -> list[Document]:
        """ Asynchronously get a list of documents in a collection.

        If both `collection_name` and `collection_id` are provided, `collection_id` will be used.

        Args:
            collection_name (str): The name of the collection to get documents from. Defaults to "default".
            collection_id (str): The ID of the collection to get documents from. Defaults to None. If provided,
                `collection_name` will be ignored.
            limit (int): The maximum number of documents to return. Defaults to 100. Maximum allowed is 1000.
            offset (int): The offset to start from. Defaults to 0.

        Returns:
            Documents: A list of documents in a collection.
        """
        if collection_id is not None:
            r = await self.aclient.get(f"/collections/{collection_id}/documents",
                                       params={"limit": limit, "offset": offset})
        else:
            r = await self.aclient.get("/documents",
                                       params={
                                           "collection_name": collection_name,
                                           "limit": limit,
                                           "offset": offset
                                       })
        handle_response(r)
        return [Document(**document, client=self._lexy_client) for document in r.json()]

    def add_documents(self,
                      docs: Document | dict | list[Document | dict],
                      *,
                      collection_name: str = "default",
                      collection_id: str = None,
                      batch_size: int = 100) -> list[Document]:
        """ Synchronously add documents to a collection in batches.

        If both `collection_name` and `collection_id` are provided, `collection_id` will be used.

        Args:
            docs (Document | dict | list[Document | dict]): The documents to add.
            collection_name (str): The name of the collection to add the documents to. Defaults to "default".
            collection_id (str): The ID of the collection to add the documents to. Defaults to None. If provided,
                `collection_name` will be ignored.
            batch_size (int): The number of documents to add in each batch. Defaults to 100.

        Returns:
            Documents: A list of created documents.

        Examples:
            Add documents to the default collection:

            >>> from lexy_py import LexyClient
            >>> lx = LexyClient()
            >>> docs_added = lx.add_documents(docs=[
            ...     {"content": "Default document 1"},
            ...     {"content": "Default document 2"}
            ... ])

            Add documents to a specific collection by name:

            >>> my_new_collection = lx.create_collection("my_new_collection")
            >>> docs_added = lx.add_documents(docs=[
            ...     {"content": "My first document"},
            ...     {"content": "My second document"}
            ... ], collection_name="my_new_collection")

            Add documents to a specific collection by ID:

            >>> docs_added = lx.add_documents(docs=[
            ...     {"content": "My third document"},
            ...     {"content": "My fourth document"}
            ... ], collection_id=my_new_collection.collection_id)

        """
        created_docs = []
        processed_docs = self._process_docs(docs)

        for i in range(0, len(processed_docs), batch_size):
            batch_docs = processed_docs[i:i + batch_size]

            if collection_id is not None:
                r = self.client.post(f"/collections/{collection_id}/documents", json=batch_docs)
            else:
                r = self.client.post("/documents", json=batch_docs, params={"collection_name": collection_name})

            handle_response(r)
            created_docs.extend(
                [Document(**document['document'], client=self._lexy_client) for document in r.json()]
            )
        return created_docs

    async def aadd_documents(self,
                             docs: Document | dict | list[Document | dict],
                             *,
                             collection_name: str = "default",
                             collection_id: str = None,
                             batch_size: int = 100) -> list[Document]:
        """ Asynchronously add documents to a collection in batches.

        If both `collection_name` and `collection_id` are provided, `collection_id` will be used.

        Args:
            docs (Document | dict | list[Document | dict]): The documents to add.
            collection_name (str): The name of the collection to add the documents to. Defaults to "default".
            collection_id (str): The ID of the collection to add the documents to. Defaults to None. If provided,
                `collection_name` will be ignored.
            batch_size (int): The number of documents to add in each batch. Defaults to 100.

        Returns:
            Documents: A list of created documents.
        """
        created_docs = []
        processed_docs = self._process_docs(docs)

        for i in range(0, len(processed_docs), batch_size):
            batch_docs = processed_docs[i:i + batch_size]

            if collection_id is not None:
                r = await self.aclient.post(f"/collections/{collection_id}/documents", json=batch_docs)
            else:
                r = await self.aclient.post("/documents", json=batch_docs,
                                            params={"collection_name": collection_name})

            handle_response(r)
            created_docs.extend(
                [Document(**document['document'], client=self._lexy_client) for document in r.json()]
            )
        return created_docs

    def add_document(self,
                     doc: Document | dict,
                     *,
                     collection_name: str = "default",
                     collection_id: str = None) -> Document:
        """ Synchronously add a document to a collection.

        If both `collection_name` and `collection_id` are provided, `collection_id` will be used.

        Args:
            doc (Document | dict): The document to add.
            collection_name (str): The name of the collection to add the document to. Defaults to "default".
            collection_id (str): The ID of the collection to add the document to. If provided, `collection_name` will
                be ignored.

        Returns:
            Document: The created document.
        """
        processed_docs = self._process_docs(doc)

        if collection_id is not None:
            r = self.client.post(f"/collections/{collection_id}/documents", json=processed_docs)
        else:
            r = self.client.post("/documents", json=processed_docs, params={"collection_name": collection_name})

        handle_response(r)
        return Document(**r.json()[0]['document'], client=self._lexy_client)

    async def aadd_document(self,
                            doc: Document | dict,
                            *,
                            collection_name: str = "default",
                            collection_id: str = None) -> Document:
        """ Asynchronously add a document to a collection.

        If both `collection_name` and `collection_id` are provided, `collection_id` will be used.

        Args:
            doc (Document | dict): The document to add.
            collection_name (str): The name of the collection to add the document to. Defaults to "default".
            collection_id (str): The ID of the collection to add the document to. If provided, `collection_name` will
                be ignored.

        Returns:
            Document: The created document.
        """
        processed_docs = self._process_docs(doc)

        if collection_id is not None:
            r = await self.aclient.post(f"/collections/{collection_id}/documents", json=processed_docs)
        else:
            r = await self.aclient.post("/documents", json=processed_docs,
                                        params={"collection_name": collection_name})

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

    def update_document(self,
                        document_id: str,
                        *,
                        content: Optional[str] = None,
                        meta: Optional[dict] = None) -> Document:
        """ Synchronously update a document.

        Args:
            document_id (str): The ID of the document to update.
            content (str, optional): The new content of the document.
            meta (dict, optional): The new metadata for the document.

        Returns:
            Document: The updated document.
        """
        document = DocumentUpdate(content=content, meta=meta)
        r = self.client.patch(f"/documents/{document_id}", json=document.model_dump(exclude_none=True))
        handle_response(r)
        return Document(**r.json()['document'], client=self._lexy_client)

    async def aupdate_document(self,
                               document_id: str,
                               *,
                               content: Optional[str] = None,
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
        r = await self.aclient.patch(f"/documents/{document_id}", json=document.model_dump(exclude_none=True))
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

    def bulk_delete_documents(self,
                              *,
                              collection_name: str = None,
                              collection_id: str = None) -> dict:
        """ Synchronously delete all documents from a collection.

        If both `collection_name` and `collection_id` are provided, `collection_id` will be used.

        Args:
            collection_name (str): The name of the collection to delete documents from.
            collection_id (str): The ID of the collection to delete documents from. If provided, `collection_name`
                will be ignored.

        Raises:
            ValueError: If neither `collection_name` nor `collection_id` are provided.
        """
        if collection_id:
            r = self.client.delete(f"/collections/{collection_id}/documents")
        elif collection_name:
            r = self.client.delete("/documents", params={"collection_name": collection_name})
        else:
            raise ValueError("Either 'collection_name' or 'collection_id' must be provided")
        handle_response(r)
        return r.json()

    def upload_documents(self,
                         files: str | Image.Image | list[str | Image.Image],
                         filenames: str | list[str] = None,
                         *,
                         collection_name: str = "default",
                         collection_id: str = None,
                         batch_size: int = 5) -> list[Document]:
        """ Synchronously upload files to a collection in batches.

        If both `collection_name` and `collection_id` are provided, `collection_id` will be used.

        Args:
            files (str | Image.Image | list[str | Image.Image]): The files to upload. Can be a single instance or a
                list of a string containing the path to a file or an `Image.Image` object.
            filenames (str | list[str], optional): The filenames of the files to upload. Defaults to None.
            collection_name (str): The name of the collection to upload the files to. Defaults to "default".
            collection_id (str): The ID of the collection to upload the files to. Defaults to None. If provided,
                `collection_name` will be ignored.
            batch_size (int): The number of files to upload in each batch. Defaults to 5.

        Returns:
            Documents: A list of created documents.

        Raises:
            TypeError: If an input file type is invalid.
            ValueError: If the length of the filenames list does not match the length of the files list.

        Examples:

            >>> from lexy_py import LexyClient
            >>> lx = LexyClient()
            >>> lx.document.upload_documents(
            ...     files=[
            ...         'lexy/sample_data/images/lexy-dalle.jpeg',
            ...         'lexy/sample_data/images/lexy.png',
            ...         'dais2023-233180.pdf',
            ...         'gwdemo30.mp4',
            ...         'kindle2.html',
            ...     ],
            ...     collection_name='my_file_collection',
            ... )

        """
        created_docs = []
        files, filenames = self._align_filenames(files, filenames)

        # process and upload files in batches
        for i in range(0, len(files), batch_size):
            batch_files = files[i:i + batch_size]
            batch_filenames = filenames[i:i + batch_size]
            processed_files = self._process_files(batch_files, filenames=batch_filenames)

            if collection_id is not None:
                r = self.client.post(f"/collections/{collection_id}/documents/upload",
                                     files=processed_files)
            else:
                r = self.client.post("/documents/upload",
                                     files=processed_files,
                                     params={"collection_name": collection_name})

            handle_response(r)
            created_docs.extend(
                [Document(**document['document'], client=self._lexy_client) for document in r.json()]
            )
        return created_docs

    async def aupload_documents(self,
                                files: str | Image.Image | list[str | Image.Image],
                                filenames: str | list[str] = None,
                                *,
                                collection_name: str = "default",
                                collection_id: str = None,
                                batch_size: int = 5) -> list[Document]:
        """ Asynchronously upload files to a collection in batches.

        If both `collection_name` and `collection_id` are provided, `collection_id` will be used.

        Args:
            files (str | Image.Image | list[str | Image.Image]): The files to upload. Can be a single instance or a
                list of a string containing the path to a file or an `Image.Image` object.
            filenames (str | list[str], optional): The filenames of the files to upload. Defaults to None.
            collection_name (str): The name of the collection to upload the files to. Defaults to "default".
            collection_id (str): The ID of the collection to upload the files to. Defaults to None. If provided,
                `collection_name` will be ignored.
            batch_size (int): The number of files to upload in each batch. Defaults to 5.

        Returns:
            Documents: A list of created documents.

        Raises:
            TypeError: If an input file type is invalid.
            ValueError: If the length of the filenames list does not match the length of the files list.
        """
        created_docs = []
        files, filenames = self._align_filenames(files, filenames)

        # process and upload files in batches
        for i in range(0, len(files), batch_size):
            batch_files = files[i:i + batch_size]
            batch_filenames = filenames[i:i + batch_size]
            processed_files = self._process_files(batch_files, filenames=batch_filenames)

            if collection_id is not None:
                r = await self.aclient.post(f"/collections/{collection_id}/documents/upload",
                                            files=processed_files)
            else:
                r = await self.aclient.post("/documents/upload",
                                            files=processed_files,
                                            params={"collection_name": collection_name})

            handle_response(r)
            created_docs.extend(
                [Document(**document['document'], client=self._lexy_client) for document in r.json()]
            )
        return created_docs

    def get_document_urls(self, document_id: str, *, expiration: int = 3600) -> dict:
        """ Synchronously get presigned URLs for a document.

        Args:
            document_id (str): The ID of the document to get presigned URL for.
            expiration (int): The expiration time of the presigned URLs in seconds. Defaults to 3600.

        Returns:
            dict: A dictionary containing presigned URLs.

        Examples:
            >>> from lexy_py import LexyClient
            >>> lx = LexyClient()
            >>> my_image_document = lx.list_documents('my_image_collection', limit=1)[0]
            >>> lx.document.get_document_urls(document_id=my_image_document.document_id)
            {
                "object": "https://my-bucket.s3.amazonaws.com/path/to/object?...",
                "thumbnails": {
                    "256x256": "https://my-bucket.s3.amazonaws.com/path/to/thumbnail?..."
                }
            }

            >>> my_pdf_document = lx.list_documents('pdf_collection', limit=1)[0]
            >>> lx.document.get_document_urls(document_id=my_pdf_document.document_id)
            {
                "object": "https://my-bucket.s3.amazonaws.com/path/to/object?...",
            }
        """
        r = self.client.get(f"/documents/{document_id}/urls", params={"expiration": expiration})
        handle_response(r)
        return r.json()

    async def aget_document_urls(self, document_id: str, *, expiration: int = 3600) -> dict:
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
                processed_docs.append(doc.model_dump(mode='json'))
            elif isinstance(doc, dict):
                doc = Document(**doc)
                processed_docs.append(doc.model_dump(mode='json'))
            else:
                raise TypeError(f"Invalid type for doc item: {type(doc)} - must be Document or dict")

        return processed_docs

    @staticmethod
    def _process_files(files: str | Image.Image | list[str | Image.Image],
                       filenames: str | list[str] = None) -> list:
        processed_files = []
        files, filenames = DocumentClient._align_filenames(files, filenames)

        for file, filename in zip(files, filenames):
            if isinstance(file, str):
                with open(file, 'rb') as f:
                    file_content = f.read()
                if not filename:
                    filename = os.path.basename(file)
            elif isinstance(file, Image.Image):
                buffer = BytesIO()
                image_format = file.format or 'jpg'
                file.save(buffer, format=image_format)
                buffer.seek(0)
                file_content = buffer.getvalue()
                if not filename:
                    filename = f'image.{file.format.lower()}' if file.format else 'image.jpg'
            else:
                raise TypeError(f"Invalid type for file: {type(file)} - must be a str path to a file, or an "
                                f"`Image.Image` object")

            mime_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
            processed_files.append(('files', (filename, BytesIO(file_content), mime_type)))

        return processed_files
