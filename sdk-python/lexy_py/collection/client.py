"""Client for interacting with the Collection API."""

from typing import Optional, TYPE_CHECKING

import httpx

from lexy_py.exceptions import handle_response
from .models import Collection, CollectionUpdate

if TYPE_CHECKING:
    from lexy_py.client import LexyClient


class CollectionClient:
    """
    This class is used to interact with the Lexy Collection API.

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

    def list_collections(self) -> list[Collection]:
        """Synchronously get a list of all collections.

        Returns:
            list[Collection]: A list of all collections.
        """
        r = self.client.get("/collections")
        handle_response(r)
        return [
            Collection(**collection, client=self._lexy_client)
            for collection in r.json()
        ]

    async def alist_collections(self) -> list[Collection]:
        """Asynchronously get a list of all collections.

        Returns:
            list[Collection]: A list of all collections.
        """
        r = await self.aclient.get("/collections")
        handle_response(r)
        return [
            Collection(**collection, client=self._lexy_client)
            for collection in r.json()
        ]

    def get_collection(
        self, *, collection_name: str = None, collection_id: str = None
    ) -> Collection:
        """Synchronously get a collection by name or ID.

        If both `collection_name` and `collection_id` are provided, `collection_id` will be used.

        Args:
            collection_name (str): The name of the collection to get.
            collection_id (str): The ID of the collection to get. If provided, `collection_name` will be ignored.

        Returns:
            Collection: The collection.

        Raises:
            ValueError: If neither `collection_name` nor `collection_id` are provided.

        Examples:
            >>> from lexy_py import LexyClient
            >>> lx = LexyClient()
            >>> lx.get_collection(collection_id="70b8ce75")
            <Collection('test_collection', id='70b8ce75', description='My Test Collection')>

            >>> lx.get_collection(collection_name="test_collection")
            <Collection('test_collection', id='70b8ce75', description='My Test Collection')>
        """
        if collection_id:
            return self.get_collection_by_id(collection_id)
        elif collection_name:
            return self.get_collection_by_name(collection_name)
        else:
            raise ValueError(
                "Either collection_id or collection_name must be provided."
            )

    async def aget_collection(
        self, *, collection_name: str = None, collection_id: str = None
    ) -> Collection:
        """Asynchronously get a collection by name or ID.

        If both `collection_name` and `collection_id` are provided, `collection_id` will be used.

        Args:
            collection_name (str): The name of the collection to get.
            collection_id (str): The ID of the collection to get. If provided, `collection_name` will be ignored.

        Returns:
            Collection: The collection.

        Raises:
            ValueError: If neither `collection_name` nor `collection_id` are provided.
        """
        if collection_id:
            return await self.aget_collection_by_id(collection_id)
        elif collection_name:
            return await self.aget_collection_by_name(collection_name)
        else:
            raise ValueError(
                "Either 'collection_name' or 'collection_id' must be provided."
            )

    def get_collection_by_id(self, collection_id: str) -> Collection:
        """Synchronously get a collection by ID.

        Args:
            collection_id (str): The ID of the collection to get.

        Returns:
            Collection: The collection.
        """
        r = self.client.get(f"/collections/{collection_id}")
        handle_response(r)
        return Collection(**r.json(), client=self._lexy_client)

    async def aget_collection_by_id(self, collection_id: str) -> Collection:
        """Asynchronously get a collection by ID.

        Args:
            collection_id (str): The ID of the collection to get.

        Returns:
            Collection: The collection.
        """
        r = await self.aclient.get(f"/collections/{collection_id}")
        handle_response(r)
        return Collection(**r.json(), client=self._lexy_client)

    def get_collection_by_name(self, collection_name: str) -> Collection:
        """Synchronously get a collection by name.

        Args:
            collection_name (str): The name of the collection to get.

        Returns:
            Collection: The collection.
        """
        r = self.client.get(
            url="/collections", params={"collection_name": collection_name}
        )
        handle_response(r)
        return Collection(**r.json(), client=self._lexy_client)

    async def aget_collection_by_name(self, collection_name: str) -> Collection:
        """Asynchronously get a collection by name.

        Args:
            collection_name (str): The name of the collection to get.

        Returns:
            Collection: The collection.
        """
        r = await self.aclient.get(
            url="/collections", params={"collection_name": collection_name}
        )
        handle_response(r)
        return Collection(**r.json(), client=self._lexy_client)

    def create_collection(
        self,
        collection_name: str,
        *,
        description: Optional[str] = None,
        config: Optional[dict] = None,
    ) -> Collection:
        """Synchronously create a new collection.

        Args:
            collection_name (str): The name of the collection to create. Collection
                names must be unique.
            description (str, optional): The description of the collection. Defaults to
                None.
            config (dict, optional): The config of the collection. Defaults to None.

        Returns:
            Collection: The created collection.

        Examples:
            >>> from lexy_py import LexyClient
            >>> lx = LexyClient()
            >>> lx.create_collection("test_collection", description="My Test Collection")
            <Collection('test_collection', id='70b8ce75', description='My Test Collection')>

            >>> lx.create_collection(collection_name="no_files",
            ...                      description="Collection without files",
            ...                      config={"store_files": False})
            <Collection('no_files', id='925d40ac', description='Collection without files')>
        """
        collection = Collection(
            collection_name=collection_name, description=description, config=config
        )
        r = self.client.post(
            url="/collections", json=collection.model_dump(exclude_none=True)
        )
        handle_response(r)
        return Collection(**r.json(), client=self._lexy_client)

    async def acreate_collection(
        self,
        collection_name: str,
        *,
        description: Optional[str] = None,
        config: Optional[dict] = None,
    ) -> Collection:
        """Asynchronously create a new collection.

        Args:
            collection_name (str): The name of the collection to create. Collection
                names must be unique.
            description (str, optional): The description of the collection. Defaults to
                None.
            config (dict, optional): The config of the collection. Defaults to None.

        Returns:
            Collection: The created collection.
        """
        collection = Collection(
            collection_name=collection_name, description=description, config=config
        )
        r = await self.aclient.post(
            url="/collections", json=collection.model_dump(exclude_none=True)
        )
        handle_response(r)
        return Collection(**r.json(), client=self._lexy_client)

    def update_collection(
        self,
        *,
        collection_id: str,
        collection_name: Optional[str] = None,
        description: Optional[str] = None,
        config: Optional[dict] = None,
    ) -> Collection:
        """Synchronously update a collection.

        Args:
            collection_id (str): The ID of the collection to update.
            collection_name (str, optional): The updated name of the collection. Defaults to None.
            description (str, optional): The updated description of the collection. Defaults to None.
            config: (dict, optional): The updated config of the collection. Defaults to None.

        Returns:
            Collection: The updated collection.
        """
        collection = CollectionUpdate(
            collection_name=collection_name, description=description, config=config
        )
        r = self.client.patch(
            url=f"/collections/{collection_id}",
            json=collection.model_dump(exclude_none=True),
        )
        handle_response(r)
        return Collection(**r.json(), client=self._lexy_client)

    async def aupdate_collection(
        self,
        *,
        collection_id: str,
        collection_name: Optional[str] = None,
        description: Optional[str] = None,
        config: Optional[dict] = None,
    ) -> Collection:
        """Asynchronously update a collection.

        Args:
            collection_id (str): The ID of the collection to update.
            collection_name (str, optional): The updated name of the collection. Defaults to None.
            description (str, optional): The updated description of the collection. Defaults to None.
            config: (dict, optional): The updated config of the collection. Defaults to None.

        Returns:
            Collection: The updated collection.
        """
        collection = CollectionUpdate(
            collection_name=collection_name, description=description, config=config
        )
        r = await self.aclient.patch(
            url=f"/collections/{collection_id}",
            json=collection.model_dump(exclude_none=True),
        )
        handle_response(r)
        return Collection(**r.json(), client=self._lexy_client)

    def delete_collection(
        self,
        *,
        collection_name: str = None,
        collection_id: str = None,
        delete_documents: bool = False,
    ) -> dict:
        """Synchronously delete a collection by name or ID.

        If both `collection_name` and `collection_id` are provided, `collection_id` will be used.

        Args:
            collection_name (str): The name of the collection to delete.
            collection_id (str): The ID of the collection to delete. If provided, `collection_name` will be ignored.
            delete_documents (bool, optional): Whether to delete the documents in the collection. Defaults to False.

        Raises:
            ValueError: If neither `collection_name` nor `collection_id` are provided.

        Examples:
            >>> from lexy_py import LexyClient
            >>> lx = LexyClient()
            >>> lx.delete_collection(collection_name="test_collection", delete_documents=True)
            {"msg": "Collection deleted", "collection_id": "70b8ce75", "documents_deleted": 3}
        """
        if collection_id:
            r = self.client.delete(
                url=f"/collections/{collection_id}",
                params={"delete_documents": delete_documents},
            )
        elif collection_name:
            r = self.client.delete(
                url="/collections",
                params={
                    "collection_name": collection_name,
                    "delete_documents": delete_documents,
                },
            )
        else:
            raise ValueError(
                "Either 'collection_name' or 'collection_id' must be provided."
            )
        handle_response(r)
        return r.json()

    async def adelete_collection(
        self,
        *,
        collection_name: str = None,
        collection_id: str = None,
        delete_documents: bool = False,
    ) -> dict:
        """Asynchronously delete a collection by name or ID.

        If both `collection_name` and `collection_id` are provided, `collection_id` will be used.

        Args:
            collection_name (str): The name of the collection to delete.
            collection_id (str): The ID of the collection to delete. If provided, `collection_name` will be ignored.
            delete_documents (bool, optional): Whether to delete the documents in the collection. Defaults to False.

        Raises:
            ValueError: If neither `collection_name` nor `collection_id` are provided.
        """
        if collection_id:
            r = await self.aclient.delete(
                url=f"/collections/{collection_id}",
                params={"delete_documents": delete_documents},
            )
        elif collection_name:
            r = await self.aclient.delete(
                url="/collections",
                params={
                    "collection_name": collection_name,
                    "delete_documents": delete_documents,
                },
            )
        else:
            raise ValueError(
                "Either 'collection_name' or 'collection_id' must be provided."
            )
        handle_response(r)
        return r.json()
