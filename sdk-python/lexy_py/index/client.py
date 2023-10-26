""" Client for interacting with the Indexes API. """

from typing import Any, Optional

import httpx

from .models import Index, IndexUpdate


class IndexClient:
    """
    This class is used to interact with the Lexy Indexes API.

    Attributes:
        aclient (httpx.AsyncClient): Asynchronous API client.
        client (httpx.Client): Synchronous API client.
    """

    def __init__(self, aclient: httpx.AsyncClient, client: httpx.Client) -> None:
        self.aclient = aclient
        self.client = client

    def list_indexes(self) -> list[Index]:
        """ Synchronously get a list of all indexes.

        Returns:
            list[Index]: A list of all indexes.
        """
        r = self.client.get("/indexes")
        return [Index(**index) for index in r.json()]

    async def alist_indexes(self) -> list[Index]:
        """ Asynchronously get a list of all indexes.

        Returns:
            list[Index]: A list of all indexes.
        """
        r = await self.aclient.get("/indexes")
        return [Index(**index) for index in r.json()]

    def get_index(self, index_id: str) -> Index:
        """ Synchronously get an index.

        Args:
            index_id (str): The ID of the index to get.

        Returns:
            Index: The index.
        """
        r = self.client.get(f"/indexes/{index_id}")
        return Index(**r.json())

    async def aget_index(self, index_id: str) -> Index:
        """ Asynchronously get an index.

        Args:
            index_id (str): The ID of the index to get.

        Returns:
            Index: The index.
        """
        r = await self.aclient.get(f"/indexes/{index_id}")
        return Index(**r.json())

    def add_index(self, index_id: str, description: Optional[str] = None,
                  index_table_schema: dict[str, Any] | None = None,
                  index_fields: dict[str, Any] | None = None) -> Index:
        """ Synchronously add an index.

        Args:
            index_id (str): The ID of the index to add.
            description (str, optional): A description of the index. Defaults to None.
            index_table_schema (dict[str, Any]): The schema of the index table. Defaults to None.
            index_fields (dict[str, Any]): The index fields that are created in the index table. These are typically
                the fields you want to populate using transformers. Defaults to None.

        Returns:
            Index: The index.

        Example:
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
        return Index(**r.json())

    async def aadd_index(self, index_id: str, description: Optional[str] = None,
                         index_table_schema: dict[str, Any] | None = None,
                         index_fields: dict[str, Any] | None = None) -> Index:
        """ Asynchronously add an index.

        Args:
            index_id (str): The ID of the index to add.
            description (str, optional): A description of the index. Defaults to None.
            index_table_schema (dict[str, Any]): The schema of the index table. Defaults to None.
            index_fields (dict[str, Any]): The index fields that are created in the index table. These are typically
                the fields you want to populate using transformers. Defaults to None.

        Returns:
            Index: The index.

        Example:
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
        return Index(**r.json())

    def delete_index(self, index_id: str) -> dict:
        """ Synchronously delete an index.

        Args:
            index_id (str): The ID of the index to delete.
        """
        r = self.client.delete(f"/indexes/{index_id}")
        return r.json()

    async def adelete_index(self, index_id: str) -> dict:
        """ Asynchronously delete an index.

        Args:
            index_id (str): The ID of the index to delete.
        """
        r = await self.aclient.delete(f"/indexes/{index_id}")
        return r.json()

    def update_index(self, index_id: str, description: Optional[str] = None,
                     index_table_schema: dict[str, Any] | None = None,
                     index_fields: dict[str, Any] | None = None) -> Index:
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
        return Index(**r.json())

    async def aupdate_index(self, index_id: str, description: Optional[str] = None,
                            index_table_schema: dict[str, Any] | None = None,
                            index_fields: dict[str, Any] | None = None) -> Index:
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
        return Index(**r.json())

    def list_index_records(self, index_id: str) -> list[dict]:
        """ Synchronously get a list of all index records for an index.

        Args:
            index_id (str): The ID of the index to get records for.

        Returns:
            list[dict]: A list of all index records for an index.
        """
        r = self.client.get(f"/indexes/{index_id}/records")
        return r.json()

    async def alist_index_records(self, index_id: str) -> list[dict]:
        """ Asynchronously get a list of all index records for an index.

        Args:
            index_id (str): The ID of the index to get records for.

        Returns:
            list[dict]: A list of all index records for an index.
        """
        r = await self.aclient.get(f"/indexes/{index_id}/records")
        return r.json()

    def query_index(self, index_id: str, query_string: str, k: int = 5, query_field: str = "embedding") -> list[dict]:
        """ Synchronously query an index.

        Args:
            index_id (str): The ID of the index to query.
            query_string (str): The query string.
            k (int, optional): The number of records to return. Defaults to 5.
            query_field (str, optional): The field to query. Defaults to "embedding".

        Returns:
            list[dict]: The query results.
        """
        params = {
            "query_string": query_string,
            "k": k,
            "query_field": query_field
        }
        r = self.client.get(f"/indexes/{index_id}/records/query", params=params)
        return r.json()["search_results"]

    async def aquery_index(self, index_id: str, query_string: str, k: int = 5, query_field: str = "embedding") \
            -> list[dict]:
        """ Asynchronously query an index.

        Args:
            index_id (str): The ID of the index to query.
            query_string (str): The query string.
            k (int, optional): The number of records to return. Defaults to 5.
            query_field (str, optional): The field to query. Defaults to "embedding".

        Returns:
            list[dict]: The query results.
        """
        params = {
            "query_string": query_string,
            "k": k,
            "query_field": query_field
        }
        r = await self.aclient.get(f"/indexes/{index_id}/records/query", params=params)
        return r.json()["search_results"]

