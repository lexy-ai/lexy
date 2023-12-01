""" Client for interacting with the Indexes API. """

from typing import Any, Optional, TYPE_CHECKING

import httpx

from lexy_py.exceptions import handle_response
from .models import Index, IndexUpdate

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
        self.aclient = self._lexy_client.aclient
        self.client = self._lexy_client.client

    def list_indexes(self) -> list[Index]:
        """ Synchronously get a list of all indexes.

        Returns:
            list[Index]: A list of all indexes.
        """
        r = self.client.get("/indexes")
        handle_response(r)
        return [Index(**index, client=self._lexy_client) for index in r.json()]

    async def alist_indexes(self) -> list[Index]:
        """ Asynchronously get a list of all indexes.

        Returns:
            list[Index]: A list of all indexes.
        """
        r = await self.aclient.get("/indexes")
        handle_response(r)
        return [Index(**index, client=self._lexy_client) for index in r.json()]

    def get_index(self, index_id: str) -> Index:
        """ Synchronously get an index.

        Args:
            index_id (str): The ID of the index to get.

        Returns:
            Index: The index.
        """
        r = self.client.get(f"/indexes/{index_id}")
        handle_response(r)
        return Index(**r.json(), client=self._lexy_client)

    async def aget_index(self, index_id: str) -> Index:
        """ Asynchronously get an index.

        Args:
            index_id (str): The ID of the index to get.

        Returns:
            Index: The index.
        """
        r = await self.aclient.get(f"/indexes/{index_id}")
        handle_response(r)
        return Index(**r.json(), client=self._lexy_client)

    def add_index(self, index_id: str, description: Optional[str] = None,
                  index_table_schema: Optional[dict[str, Any]] = None,
                  index_fields: Optional[dict[str, Any]] = None) -> Index:
        """ Synchronously add an index.

        Args:
            index_id (str): The ID of the index to add.
            description (str, optional): A description of the index. Defaults to None.
            index_table_schema (dict[str, Any]): The schema of the index table. Defaults to None.
            index_fields (dict[str, Any]): The index fields that are created in the index table. These are typically
                the fields you want to populate using transformers. Defaults to None.

        Returns:
            Index: The index.

        Examples:
            >>> code_index_fields = {
            ...     "code": {"type": "text"},
            ...     "code_embedding": {"type": "embedding", "extras": {"dims": 384, "distance": "cosine"}},
            ...     "n_lines": {"type": "int"},
            ... }
            >>> index = lexy.index.add_index(index_id="code_index",
            ...                              description="Code embedding index",
            ...                              index_fields=code_index_fields)
        """
        if index_table_schema is None:
            index_table_schema = {}
        if index_fields is None:
            index_fields = {}
        data = {
            "index_id": index_id,
            "description": description,
            "index_table_schema": index_table_schema,
            "index_fields": index_fields
        }
        r = self.client.post("/indexes", json=data)
        handle_response(r)
        return Index(**r.json(), client=self._lexy_client)

    async def aadd_index(self, index_id: str, description: Optional[str] = None,
                         index_table_schema: Optional[dict[str, Any]] = None,
                         index_fields: Optional[dict[str, Any]] = None) -> Index:
        """ Asynchronously add an index.

        Args:
            index_id (str): The ID of the index to add.
            description (str, optional): A description of the index. Defaults to None.
            index_table_schema (dict[str, Any]): The schema of the index table. Defaults to None.
            index_fields (dict[str, Any]): The index fields that are created in the index table. These are typically
                the fields you want to populate using transformers. Defaults to None.

        Returns:
            Index: The index.

        Examples:
            >>> code_index_fields = {
            ...     "code": {"type": "text"},
            ...     "code_embedding": {"type": "embedding", "extras": {"dims": 384, "distance": "cosine"}},
            ...     "n_lines": {"type": "int"},
            ... }
            >>> index = await lexy.index.aadd_index(index_id="code_index",
            ...                                     description="Code embedding index",
            ...                                     index_fields=code_index_fields)
        """
        if index_table_schema is None:
            index_table_schema = {}
        if index_fields is None:
            index_fields = {}
        data = {
            "index_id": index_id,
            "description": description,
            "index_table_schema": index_table_schema,
            "index_fields": index_fields
        }
        r = await self.aclient.post("/indexes", json=data)
        handle_response(r)
        return Index(**r.json(), client=self._lexy_client)

    def delete_index(self, index_id: str, drop_table: bool = False) -> dict:
        """ Synchronously delete an index.

        Args:
            index_id (str): The ID of the index to delete.
            drop_table (bool, optional): Whether to drop the index table from the database. Defaults to False.
        """
        r = self.client.delete(f"/indexes/{index_id}", params={"drop_table": drop_table})
        handle_response(r)
        return r.json()

    async def adelete_index(self, index_id: str, drop_table: bool = False) -> dict:
        """ Asynchronously delete an index.

        Args:
            index_id (str): The ID of the index to delete.
            drop_table (bool, optional): Whether to drop the index table from the database. Defaults to False.
        """
        r = await self.aclient.delete(f"/indexes/{index_id}", params={"drop_table": drop_table})
        handle_response(r)
        return r.json()

    def update_index(self, index_id: str, description: Optional[str] = None,
                     index_table_schema: Optional[dict[str, Any]] = None,
                     index_fields: Optional[dict[str, Any]] = None) -> Index:
        """ Synchronously update an index.

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
            index_fields=index_fields
        )
        r = self.client.patch(f"/indexes/{index_id}", json=index.dict(exclude_none=True))
        handle_response(r)
        return Index(**r.json(), client=self._lexy_client)

    async def aupdate_index(self, index_id: str, description: Optional[str] = None,
                            index_table_schema: Optional[dict[str, Any]] = None,
                            index_fields: Optional[dict[str, Any]] = None) -> Index:
        """ Asynchronously update an index.

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
            index_fields=index_fields
        )
        r = await self.aclient.patch(f"/indexes/{index_id}", json=index.dict(exclude_none=True))
        handle_response(r)
        return Index(**r.json(), client=self._lexy_client)

    def list_index_records(self, index_id: str, document_id: Optional[str] = None) -> list[dict]:
        """ Synchronously get a list of all index records for an index.

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

    async def alist_index_records(self, index_id: str, document_id: Optional[str] = None) -> list[dict]:
        """ Asynchronously get a list of all index records for an index.

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

    def query_index(self, query_string: str, index_id: str = "default_text_embeddings", query_field: str = "embedding",
                    k: int = 5) -> list[dict]:
        """ Synchronously query an index.

        Args:
            query_string (str): The query string.
            index_id (str): The ID of the index to query. Defaults to "default_text_embeddings".
            query_field (str, optional): The field to query. Defaults to "embedding".
            k (int, optional): The number of records to return. Defaults to 5.

        Returns:
            list[dict]: The query results.
        """
        params = {
            "query_string": query_string,
            "query_field": query_field,
            "k": k
        }
        r = self.client.get(f"/indexes/{index_id}/records/query", params=params)
        handle_response(r)
        return r.json()["search_results"]

    async def aquery_index(self, query_string: str, index_id: str = "default_text_embeddings",
                           query_field: str = "embedding", k: int = 5) \
            -> list[dict]:
        """ Asynchronously query an index.

        Args:
            query_string (str): The query string.
            index_id (str): The ID of the index to query. Defaults to "default_text_embeddings".
            query_field (str, optional): The field to query. Defaults to "embedding".
            k (int, optional): The number of records to return. Defaults to 5.

        Returns:
            list[dict]: The query results.
        """
        params = {
            "query_string": query_string,
            "query_field": query_field,
            "k": k
        }
        r = await self.aclient.get(f"/indexes/{index_id}/records/query", params=params)
        handle_response(r)
        return r.json()["search_results"]
