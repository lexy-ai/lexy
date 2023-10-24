""" Client for interacting with the Collection API. """

from typing import Optional

import httpx

from .models import Collection


class CollectionClient:
    """
    This class is used to interact with the Lexy Collection API.

    Attributes:
        aclient (httpx.AsyncClient): Asynchronous API client.
        client (httpx.Client): Synchronous API client.
    """

    def __init__(self, aclient: httpx.AsyncClient, client: httpx.Client) -> None:
        self.aclient = aclient
        self.client = client

    def list_collections(self) -> list[Collection]:
        """ Synchronously get a list of all collections.

        Returns:
            list[Collection]: A list of all collections.
        """
        r = self.client.get("/collections")
        return [Collection(**collection) for collection in r.json()]

    async def alist_collections(self) -> list[Collection]:
        """ Asynchronously get a list of all collections.

        Returns:
            list[Collection]: A list of all collections.
        """
        r = await self.aclient.get("/collections")
        return [Collection(**collection) for collection in r.json()]

    def get_collection(self, collection_id: str) -> Collection:
        """ Synchronously get a collection.

        Args:
            collection_id (str): The ID of the collection to get.

        Returns:
            Collection: The collection.
        """
        r = self.client.get(f"/collections/{collection_id}")
        return Collection(**r.json())

    async def aget_collection(self, collection_id: str) -> Collection:
        """ Asynchronously get a collection.

        Args:
            collection_id (str): The ID of the collection to get.

        Returns:
            Collection: The collection.
        """
        r = await self.aclient.get(f"/collections/{collection_id}")
        return Collection(**r.json())

    def add_collection(self, collection_id: str, description: Optional[str] = None) -> Collection:
        """ Synchronously create a new collection.

        Args:
            collection_id (str): The ID of the collection to create.
            description (Optional[str], optional): The description of the collection. Defaults to None.

        Returns:
            Collection: The created collection.
        """
        collection = Collection(
            collection_id=collection_id,
            description=description
        )
        r = self.client.post("/collections", json=collection.dict(exclude_none=True))
        return Collection(**r.json())

    async def aadd_collection(self, collection_id: str, description: Optional[str] = None) -> Collection:
        """ Asynchronously create a new collection.

        Args:
            collection_id (str): The ID of the collection to create.
            description (Optional[str], optional): The description of the collection. Defaults to None.

        Returns:
            Collection: The created collection.
        """
        collection = Collection(
            collection_id=collection_id,
            description=description
        )
        r = await self.aclient.post("/collections", json=collection.dict(exclude_none=True))
        return Collection(**r.json())
