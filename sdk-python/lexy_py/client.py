""" Client for interacting with the Lexy API. """

import httpx

from .settings import DEFAULT_BASE_URL
from .binding.client import BindingClient
from .collection.client import CollectionClient
from .document.client import DocumentClient
from .index.client import IndexClient
from .transformer.client import TransformerClient


API_TIMEOUT = 10


class LexyClient:
    """
    LexyClient class

    Attributes:
        base_url (str): Base URL for the Lexy API.
        aclient (httpx.AsyncClient): Asynchronous API client.
        client (httpx.Client): Synchronous API client.
    """

    base_url: str
    aclient: httpx.AsyncClient
    client: httpx.Client

    binding: BindingClient
    collection: CollectionClient
    document: DocumentClient
    index: IndexClient
    transformer: TransformerClient

    def __init__(self, base_url: str = DEFAULT_BASE_URL) -> None:
        self.base_url = base_url
        self.aclient = httpx.AsyncClient(base_url=self.base_url, timeout=API_TIMEOUT)
        self.client = httpx.Client(base_url=self.base_url, timeout=API_TIMEOUT)

        self.binding = BindingClient(self)
        self.collection = CollectionClient(self)
        self.document = DocumentClient(self)
        self.index = IndexClient(self)
        self.transformer = TransformerClient(self)

    async def __aenter__(self) -> "LexyClient":
        """ Async context manager entry point. """
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        """ Async context manager exit point. """
        await self.aclient.aclose()

    def __enter__(self) -> "LexyClient":
        """ Synchronous context manager entry point. """
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        """ Synchronous context manager exit point. """
        self.client.close()

    def get(self, url: str, **kwargs) -> httpx.Response:
        """ Synchronous GET request. """
        return self.client.get(url, **kwargs)

    async def aget(self, url: str, **kwargs) -> httpx.Response:
        """ Async GET request. """
        return await self.aclient.get(url, **kwargs)

    def post(self, url: str, **kwargs) -> httpx.Response:
        """ Synchronous POST request. """
        return self.client.post(url, **kwargs)

    async def apost(self, url: str, **kwargs) -> httpx.Response:
        """ Async POST request. """
        return await self.aclient.post(url, **kwargs)

    def patch(self, url: str, **kwargs) -> httpx.Response:
        """ Synchronous PATCH request. """
        return self.client.patch(url, **kwargs)

    async def apatch(self, url: str, **kwargs) -> httpx.Response:
        """ Async PATCH request. """
        return await self.aclient.patch(url, **kwargs)

    def delete(self, url: str, **kwargs) -> httpx.Response:
        """ Synchronous DELETE request. """
        return self.client.delete(url, **kwargs)

    async def adelete(self, url: str, **kwargs) -> httpx.Response:
        """ Async DELETE request. """
        return await self.aclient.delete(url, **kwargs)




