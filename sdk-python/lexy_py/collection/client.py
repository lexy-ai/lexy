""" Client for interacting with the Collection API. """

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
        """ Synchronously get a list of all collections.

        Returns:
            list[Collection]: A list of all collections.
        """
        r = self.client.get("/collections")
        handle_response(r)
        return [Collection(**collection, client=self._lexy_client) for collection in r.json()]

    async def alist_collections(self) -> list[Collection]:
        """ Asynchronously get a list of all collections.

        Returns:
            list[Collection]: A list of all collections.
        """
        r = await self.aclient.get("/collections")
        handle_response(r)
        return [Collection(**collection, client=self._lexy_client) for collection in r.json()]

    def get_collection(self, collection_id: str) -> Collection:
        """ Synchronously get a collection.

        Args:
            collection_id (str): The ID of the collection to get.

        Returns:
            Collection: The collection.
        """
        r = self.client.get(f"/collections/{collection_id}")
        handle_response(r)
        return Collection(**r.json(), client=self._lexy_client)

    async def aget_collection(self, collection_id: str) -> Collection:
        """ Asynchronously get a collection.

        Args:
            collection_id (str): The ID of the collection to get.

        Returns:
            Collection: The collection.
        """
        r = await self.aclient.get(f"/collections/{collection_id}")
        handle_response(r)
        return Collection(**r.json(), client=self._lexy_client)

    def add_collection(self,
                       collection_id: str,
                       description: Optional[str] = None,
                       config: Optional[dict] = None) -> Collection:
        """ Synchronously create a new collection.

        Args:
            collection_id (str): The ID of the collection to create.
            description (str, optional): The description of the collection. Defaults to None.
            config (dict, optional): The config of the collection. Defaults to None.

        Returns:
            Collection: The created collection.

        Examples:
            >>> from lexy_py import LexyClient
            >>> lexy = LexyClient()
            >>> lexy.create_collection("test_collection", "My Test Collection")
            Collection(collection_id='test_collection', description='My Test Collection')

            >>> lexy.create_collection(collection_id="no_files",
            ...                        description="Collection without files",
            ...                        config={"store_files": False})
            Collection(collection_id='no_files', description='Collection without files')
        """
        collection = Collection(
            collection_id=collection_id,
            description=description,
            config=config
        )
        r = self.client.post("/collections", json=collection.model_dump(exclude_none=True))
        handle_response(r)
        return Collection(**r.json(), client=self._lexy_client)

    async def aadd_collection(self,
                              collection_id: str,
                              description: Optional[str] = None,
                              config: Optional[dict] = None) -> Collection:
        """ Asynchronously create a new collection.

        Args:
            collection_id (str): The ID of the collection to create.
            description (str, optional): The description of the collection. Defaults to None.
            config (dict, optional): The config of the collection. Defaults to None.

        Returns:
            Collection: The created collection.
        """
        collection = Collection(
            collection_id=collection_id,
            description=description,
            config=config
        )
        r = await self.aclient.post("/collections", json=collection.model_dump(exclude_none=True))
        handle_response(r)
        return Collection(**r.json(), client=self._lexy_client)

    def update_collection(self,
                          collection_id: str,
                          description: Optional[str] = None,
                          config: Optional[dict] = None) -> Collection:
        """ Synchronously update a collection.

        Args:
            collection_id (str): The ID of the collection to update.
            description (str, optional): The updated description of the collection. Defaults to None.
            config: (dict, optional): The updated config of the collection. Defaults to None.

        Returns:
            Collection: The updated collection.
        """
        collection = CollectionUpdate(
            description=description,
            config=config
        )
        r = self.client.patch(f"/collections/{collection_id}", json=collection.model_dump(exclude_none=True))
        handle_response(r)
        return Collection(**r.json(), client=self._lexy_client)

    async def aupdate_collection(self,
                                 collection_id: str,
                                 description: Optional[str] = None,
                                 config: Optional[dict] = None) -> Collection:
        """ Asynchronously update a collection.

        Args:
            collection_id (str): The ID of the collection to update.
            description (str, optional): The updated description of the collection. Defaults to None.
            config: (dict, optional): The updated config of the collection. Defaults to None.

        Returns:
            Collection: The updated collection.
        """
        collection = CollectionUpdate(
            description=description,
            config=config
        )
        r = await self.aclient.patch(f"/collections/{collection_id}", json=collection.model_dump(exclude_none=True))
        handle_response(r)
        return Collection(**r.json(), client=self._lexy_client)

    def delete_collection(self, collection_id: str, delete_documents: bool = False) -> dict:
        """ Synchronously delete a collection.

        Args:
            collection_id (str): The ID of the collection to delete.
            delete_documents (bool, optional): Whether to delete the documents in the collection. Defaults to False.
        """
        r = self.client.delete(f"/collections/{collection_id}", params={"delete_documents": delete_documents})
        handle_response(r)
        return r.json()

    async def adelete_collection(self, collection_id: str, delete_documents: bool = False) -> dict:
        """ Asynchronously delete a collection.

        Args:
            collection_id (str): The ID of the collection to delete.
            delete_documents (bool, optional): Whether to delete the documents in the collection. Defaults to False.
        """
        r = await self.aclient.delete(f"/collections/{collection_id}",
                                      params={"delete_documents": delete_documents})
        handle_response(r)
        return r.json()
