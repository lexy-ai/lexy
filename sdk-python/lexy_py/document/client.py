""" Client for interacting with the Document API. """

from typing import Optional

import httpx

from .models import Document, DocumentUpdate


class DocumentClient:
    """
    This class is used to interact with the Lexy Document API.

    Attributes:
        aclient (httpx.AsyncClient): Asynchronous API client.
        client (httpx.Client): Synchronous API client.
    """

    def __init__(self, aclient: httpx.AsyncClient, client: httpx.Client) -> None:
        self.aclient = aclient
        self.client = client

    def list_documents(self, collection_id: str = "default") -> list[Document]:
        """ Synchronously get a list of all documents in a collection.

        Args:
            collection_id (str): The ID of the collection to get documents from. Defaults to "default".

        Returns:
            list[Document]: A list of all documents in a collection.
        """
        r = self.client.get("/documents", params={"collection_id": collection_id})
        return [Document(**document) for document in r.json()]

    async def alist_documents(self, collection_id: str = "default") -> list[Document]:
        """ Asynchronously get a list of all documents in a collection.

        Args:
            collection_id (str): The ID of the collection to get documents from. Defaults to "default".

        Returns:
            list[Document]: A list of all documents in a collection.
        """
        r = await self.aclient.get("/documents", params={"collection_id": collection_id})
        return [Document(**document) for document in r.json()]

    def add_documents(self, docs: Document | list[Document] | dict | list[dict],
                      collection_id: str = "default") -> list[dict]:
        """ Synchronously add documents to a collection.

        Args:
            docs (Document | list[Document] | dict | list[dict]): The documents to add.
            collection_id (str): The ID of the collection to add the documents to. Defaults to "default".

        Returns:
            list[dict]: A list of dictionaries containing created documents and their associated tasks.
        """
        processed_docs = self._process_docs(docs)

        r = self.client.post("/documents", json=processed_docs, params={"collection_id": collection_id})
        return r.json()

    async def aadd_documents(self, docs: Document | list[Document] | dict | list[dict],
                             collection_id: str = "default") -> list[dict]:
        """ Asynchronously add documents to a collection.

        Args:
            docs (Document | list[Document] | dict | list[dict]): The documents to add.
            collection_id (str): The ID of the collection to add the documents to. Defaults to "default".

        Returns:
            list[dict]: A list of dictionaries containing created documents and their associated tasks.
        """
        processed_docs = self._process_docs(docs)

        r = await self.aclient.post("/documents", json=processed_docs, params={"collection_id": collection_id})
        return r.json()

    def add_document(self, doc: Document | dict, collection_id: str) -> dict:
        """ Synchronously add a document to a collection.

        Args:
            doc (Document | dict): The document to add.
            collection_id (str): The ID of the collection to add the document to.

        Returns:
            dict: A dictionary containing the created document and its associated tasks.
        """
        processed_docs = self._process_docs(doc)

        r = self.client.post("/documents", json=processed_docs, params={"collection_id": collection_id})
        return r.json()[0]

    async def aadd_document(self, doc: Document | dict, collection_id: str) -> dict:
        """ Asynchronously add a document to a collection.

        Args:
            doc (Document | dict): The document to add.
            collection_id (str): The ID of the collection to add the document to.

        Returns:
            dict: A dictionary containing the created document and its associated tasks.
        """
        processed_docs = self._process_docs(doc)

        r = await self.aclient.post("/documents", json=processed_docs, params={"collection_id": collection_id})
        return r.json()[0]

    def get_document(self, document_id: str) -> Document:
        """ Synchronously get a document.

        Args:
            document_id (str): The ID of the document to get.

        Returns:
            Document: The document.
        """
        r = self.client.get(f"/documents/{document_id}")
        return Document(**r.json())

    async def aget_document(self, document_id: str) -> Document:
        """ Asynchronously get a document.

        Args:
            document_id (str): The ID of the document to get.

        Returns:
            Document: The document.
        """
        r = await self.aclient.get(f"/documents/{document_id}")
        return Document(**r.json())

    def update_document(self, document_id: str, title: Optional[str] = None, content: Optional[str] = None,
                        meta: Optional[dict] = None) -> dict:
        """ Synchronously update a document.

        Args:
            document_id (str): The ID of the document to update.
            title (Optional[str]): The new title of the document.
            content (Optional[str]): The new content of the document.
            meta (Optional[dict]): The new metadata for the document.

        Returns:
            dict: A dictionary containing the updated document and its associated tasks.
        """
        document = DocumentUpdate(title=title, content=content, meta=meta)
        r = self.client.patch(f"/documents/{document_id}", json=document.dict(exclude_none=True))
        return r.json()

    async def aupdate_document(self, document_id: str, title: Optional[str] = None, content: Optional[str] = None,
                               meta: Optional[dict] = None) -> dict:
        """ Asynchronously update a document.

        Args:
            document_id (str): The ID of the document to update.
            title (Optional[str]): The new title of the document.
            content (Optional[str]): The new content of the document.
            meta (Optional[dict]): The new metadata for the document.

        Returns:
            dict: A dictionary containing the updated document and its associated tasks.
        """
        document = DocumentUpdate(title=title, content=content, meta=meta)
        r = await self.aclient.patch(f"/documents/{document_id}", json=document.dict(exclude_none=True))
        return r.json()

    def delete_document(self, document_id: str) -> dict:
        """ Synchronously delete a document.

        Args:
            document_id (str): The ID of the document to delete.
        """
        r = self.client.delete(f"/documents/{document_id}")
        return r.json()

    async def adelete_document(self, document_id: str) -> dict:
        """ Asynchronously delete a document.

        Args:
            document_id (str): The ID of the document to delete.
        """
        r = await self.aclient.delete(f"/documents/{document_id}")
        return r.json()

    @staticmethod
    def _process_docs(docs: Document | list[Document] | dict | list[dict]) -> list[dict]:
        """ Process documents into a list of dictionaries. """
        processed_docs = []

        if isinstance(docs, (Document, dict)):
            docs = [docs]

        for doc in docs:
            if isinstance(doc, Document):
                processed_docs.append(doc.dict())
            elif isinstance(doc, dict):
                doc = Document(**doc)
                processed_docs.append(doc.dict())
            else:
                raise TypeError(f"Invalid type for doc item: {type(doc)} - must be Document or dict")

        return processed_docs
