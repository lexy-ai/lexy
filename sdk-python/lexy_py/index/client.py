"""Client for interacting with the Indexes API."""

import io
import os
import mimetypes
from typing import Any, Optional, TYPE_CHECKING

import httpx
from PIL import Image

from lexy_py.exceptions import handle_response, LexyClientError
from .models import Index, IndexUpdate
from lexy_py.document.models import Document

if TYPE_CHECKING:
    from lexy_py.client import LexyClient


class IndexClient:
    """
    This class is used to interact with the Lexy Indexes API.

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

    def list_indexes(self) -> list[Index]:
        """Synchronously get a list of all indexes.

        Returns:
            list[Index]: A list of all indexes.
        """
        r = self.client.get("/indexes")
        handle_response(r)
        return [Index(**index, client=self._lexy_client) for index in r.json()]

    async def alist_indexes(self) -> list[Index]:
        """Asynchronously get a list of all indexes.

        Returns:
            list[Index]: A list of all indexes.
        """
        r = await self.aclient.get("/indexes")
        handle_response(r)
        return [Index(**index, client=self._lexy_client) for index in r.json()]

    def get_index(self, index_id: str) -> Index:
        """Synchronously get an index.

        Args:
            index_id (str): The ID of the index to get.

        Returns:
            Index: The index.
        """
        r = self.client.get(f"/indexes/{index_id}")
        handle_response(r)
        return Index(**r.json(), client=self._lexy_client)

    async def aget_index(self, index_id: str) -> Index:
        """Asynchronously get an index.

        Args:
            index_id (str): The ID of the index to get.

        Returns:
            Index: The index.
        """
        r = await self.aclient.get(f"/indexes/{index_id}")
        handle_response(r)
        return Index(**r.json(), client=self._lexy_client)

    def create_index(
        self,
        index_id: str,
        description: Optional[str] = None,
        index_table_schema: Optional[dict[str, Any]] = None,
        index_fields: Optional[dict[str, Any]] = None,
    ) -> Index:
        """Synchronously create an index.

        Args:
            index_id (str): The ID of the index to create.
            description (str, optional): A description of the index. Defaults to None.
            index_table_schema (dict[str, Any]): The schema of the index table.
                Defaults to None.
            index_fields (dict[str, Any]): The index fields that are created in the
                index table. These are typically the fields you want to populate using
                transformers. Defaults to None.

        Returns:
            Index: The index.

        Examples:
            >>> from lexy_py import LexyClient
            >>> lx = LexyClient()
            >>> code_index_fields = {
            ...     "code": {"type": "text"},
            ...     "code_embedding": {"type": "embedding", "extras": {"dims": 384, "model": "text.embeddings.minilm"}},
            ...     "n_lines": {"type": "int"},
            ... }
            >>> index = lx.index.create_index(index_id="code_index",
            ...                               description="Code embedding index",
            ...                               index_fields=code_index_fields)
        """
        if index_table_schema is None:
            index_table_schema = {}
        if index_fields is None:
            index_fields = {}
        data = {
            "index_id": index_id,
            "description": description,
            "index_table_schema": index_table_schema,
            "index_fields": index_fields,
        }
        r = self.client.post("/indexes", json=data)
        handle_response(r)
        return Index(**r.json(), client=self._lexy_client)

    async def acreate_index(
        self,
        index_id: str,
        description: Optional[str] = None,
        index_table_schema: Optional[dict[str, Any]] = None,
        index_fields: Optional[dict[str, Any]] = None,
    ) -> Index:
        """Asynchronously create an index.

        Args:
            index_id (str): The ID of the index to create.
            description (str, optional): A description of the index. Defaults to None.
            index_table_schema (dict[str, Any]): The schema of the index table.
                Defaults to None.
            index_fields (dict[str, Any]): The index fields that are created in the
                index table. These are typically the fields you want to populate using
                transformers. Defaults to None.

        Returns:
            Index: The index.

        Examples:
            >>> from lexy_py import LexyClient
            >>> lx = LexyClient()
            >>> code_index_fields = {
            ...     "code": {"type": "text"},
            ...     "code_embedding": {"type": "embedding", "extras": {"dims": 384, "model": "text.embeddings.minilm"}},
            ...     "n_lines": {"type": "int"},
            ... }
            >>> index = await lx.index.acreate_index(index_id="code_index",
            ...                                      description="Code embedding index",
            ...                                      index_fields=code_index_fields)
        """
        if index_table_schema is None:
            index_table_schema = {}
        if index_fields is None:
            index_fields = {}
        data = {
            "index_id": index_id,
            "description": description,
            "index_table_schema": index_table_schema,
            "index_fields": index_fields,
        }
        r = await self.aclient.post("/indexes", json=data)
        handle_response(r)
        return Index(**r.json(), client=self._lexy_client)

    def delete_index(self, index_id: str, drop_table: bool = False) -> dict:
        """Synchronously delete an index.

        Args:
            index_id (str): The ID of the index to delete.
            drop_table (bool, optional): Whether to drop the index table from the database. Defaults to False.
        """
        r = self.client.delete(
            f"/indexes/{index_id}", params={"drop_table": drop_table}
        )
        handle_response(r)
        return r.json()

    async def adelete_index(self, index_id: str, drop_table: bool = False) -> dict:
        """Asynchronously delete an index.

        Args:
            index_id (str): The ID of the index to delete.
            drop_table (bool, optional): Whether to drop the index table from the database. Defaults to False.
        """
        r = await self.aclient.delete(
            f"/indexes/{index_id}", params={"drop_table": drop_table}
        )
        handle_response(r)
        return r.json()

    def update_index(
        self,
        index_id: str,
        description: Optional[str] = None,
        index_table_schema: Optional[dict[str, Any]] = None,
        index_fields: Optional[dict[str, Any]] = None,
    ) -> Index:
        """Synchronously update an index.

        Args:
            index_id (str): The ID of the index to update.
            description (str, optional): The new description of the index.
            index_table_schema (dict[str, Any], optional): The new schema of the index table.
            index_fields (dict[str, Any], optional): The new value for index fields that are created in the index table.

        Returns:
            Index: The updated index.
        """
        index = IndexUpdate(
            description=description,
            index_table_schema=index_table_schema,
            index_fields=index_fields,
        )
        r = self.client.patch(
            f"/indexes/{index_id}", json=index.model_dump(exclude_none=True)
        )
        handle_response(r)
        return Index(**r.json(), client=self._lexy_client)

    async def aupdate_index(
        self,
        index_id: str,
        description: Optional[str] = None,
        index_table_schema: Optional[dict[str, Any]] = None,
        index_fields: Optional[dict[str, Any]] = None,
    ) -> Index:
        """Asynchronously update an index.

        Args:
            index_id (str): The ID of the index to update.
            description (str, optional): The new description of the index.
            index_table_schema (dict[str, Any], optional): The new schema of the index table.
            index_fields (dict[str, Any], optional): The new value for index fields that are created in the index table.

        Returns:
            Index: The updated index.
        """
        index = IndexUpdate(
            description=description,
            index_table_schema=index_table_schema,
            index_fields=index_fields,
        )
        r = await self.aclient.patch(
            f"/indexes/{index_id}", json=index.model_dump(exclude_none=True)
        )
        handle_response(r)
        return Index(**r.json(), client=self._lexy_client)

    def list_index_records(
        self, index_id: str, document_id: Optional[str] = None
    ) -> list[dict]:
        """Synchronously get a list of all index records for an index.

        Args:
            index_id (str): The ID of the index to get records for.
            document_id (str, optional): The ID of a document to get records for.

        Returns:
            list[dict]: A list of all index records for an index.
        """
        params = {}
        if document_id:
            params["document_id"] = document_id
        r = self.client.get(f"/indexes/{index_id}/records", params=params)
        handle_response(r)
        return r.json()

    async def alist_index_records(
        self, index_id: str, document_id: Optional[str] = None
    ) -> list[dict]:
        """Asynchronously get a list of all index records for an index.

        Args:
            index_id (str): The ID of the index to get records for.
            document_id (str, optional): The ID of a document to get records for.

        Returns:
            list[dict]: A list of all index records for an index.
        """
        params = {}
        if document_id:
            params["document_id"] = document_id
        r = await self.aclient.get(f"/indexes/{index_id}/records", params=params)
        handle_response(r)
        return r.json()

    def query_index(
        self,
        query_text: str = None,
        query_image: Image.Image | str = None,
        index_id: str = "default_text_embeddings",
        query_field: str = "embedding",
        k: int = 5,
        return_fields: list[str] = None,
        return_document: bool = False,
        embedding_model: str = None,
    ) -> list[dict]:
        """Synchronously query an index.

        Args:
            query_text (str): The query text.
            query_image (Image.Image | str): The query image. Can be a PIL Image object or a path to an image.
            index_id (str): The ID of the index to query. Defaults to "default_text_embeddings".
            query_field (str, optional): The field to query. Defaults to "embedding".
            k (int, optional): The number of records to return. Defaults to 5.
            return_fields (list[str], optional): The fields to return. Defaults to None, which returns all fields. To
                return fields from the linked document, use "document.<field_name>".
            return_document (bool, optional): Whether to return the document object. Defaults to False.
            embedding_model (str, optional): The name of the embedding model to use. Defaults to None, which uses the
                embedding model associated with `index_id.query_field`.

        Returns:
            list[dict]: The query results.

        Examples:
            >>> from lexy_py import LexyClient
            >>> lx = LexyClient()
            >>> lx.query_index(query_text="Test Query")

            >>> lx.query_index(query_text="Test Query", return_fields=["my_index_field", "document.content"])

            >>> lx.query_index(query_image="test_image.jpg", index_id="my_image_index")

            >>> import httpx
            >>> from PIL import Image
            >>> img_url = 'https://getlexy.com/assets/images/dalle-agi.jpeg'
            >>> image = Image.open(httpx.get(img_url))
            >>> lx.query_index(query_image=image, index_id="my_image_index", k=3)
        """
        files, params = self._process_query_params(
            query_text=query_text,
            query_image=query_image,
            query_field=query_field,
            k=k,
            return_fields=return_fields,
            return_document=return_document,
            embedding_model=embedding_model,
        )

        r = self.client.post(
            f"/indexes/{index_id}/records/query", files=files, params=params
        )
        handle_response(r)
        search_results = r.json()["search_results"]
        if return_document:
            for result in search_results:
                result["document"] = Document(
                    **result["document"], client=self._lexy_client
                )
        return search_results

    async def aquery_index(
        self,
        query_text: str = None,
        query_image: Image.Image | str = None,
        index_id: str = "default_text_embeddings",
        query_field: str = "embedding",
        k: int = 5,
        return_fields: list[str] = None,
        return_document: bool = False,
        embedding_model: str = None,
    ) -> list[dict]:
        """Asynchronously query an index.

        Args:
            query_text (str): The query text.
            query_image (Image.Image | str): The query image. Can be a PIL Image object or a path to an image.
            index_id (str): The ID of the index to query. Defaults to "default_text_embeddings".
            query_field (str, optional): The field to query. Defaults to "embedding".
            k (int, optional): The number of records to return. Defaults to 5.
            return_fields (list[str], optional): The fields to return. Defaults to None, which returns all fields. To
                return fields from the linked document, use "document.<field_name>".
            return_document (bool, optional): Whether to return the document object. Defaults to False.
            embedding_model (str, optional): The name of the embedding model to use. Defaults to None, which uses the
                embedding model associated with `index_id.query_field`.

        Returns:
            list[dict]: The query results.
        """
        files, params = self._process_query_params(
            query_text=query_text,
            query_image=query_image,
            query_field=query_field,
            k=k,
            return_fields=return_fields,
            return_document=return_document,
            embedding_model=embedding_model,
        )

        r = await self.aclient.post(
            f"/indexes/{index_id}/records/query", files=files, params=params
        )
        handle_response(r)
        search_results = r.json()["search_results"]
        if return_document:
            for result in search_results:
                result["document"] = Document(
                    **result["document"], client=self._lexy_client
                )
        return search_results

    @staticmethod
    def _process_query_params(
        query_text: str,
        query_image: Image.Image | str,
        query_field: str,
        k: int,
        return_fields: list[str],
        return_document: bool,
        embedding_model: str,
    ) -> tuple[dict, dict]:
        files = {}

        if query_text and query_image:
            raise LexyClientError(
                "Please submit either 'query_text' or 'query_image', not both."
            )
        elif query_text:
            files["query_text"] = (None, query_text)
        elif query_image:
            if isinstance(query_image, str):
                image = Image.open(query_image)
                filename = os.path.basename(query_image)
            else:
                image = query_image
                filename = (
                    f"image.{image.format.lower()}" if image.format else "image.jpg"
                )
            buffer = io.BytesIO()
            image_format = image.format or "jpg"
            image.save(buffer, format=image_format)
            buffer.seek(0)
            mime_type = mimetypes.types_map.get(
                f".{image_format.lower()}", "application/octet-stream"
            )
            files["query_image"] = (filename, buffer, mime_type)
        else:
            raise LexyClientError("Please submit either 'query_text' or 'query_image'.")

        if return_fields is None:
            return_fields = []
        params = {
            "query_field": query_field,
            "k": k,
            "return_fields": return_fields,
            "return_document": return_document,
        }
        if embedding_model:
            params["embedding_model"] = embedding_model

        return files, params
