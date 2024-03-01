""" Client for interacting with the Lexy API. """

import httpx

from .settings import DEFAULT_BASE_URL
from .exceptions import LexyClientError
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
        binding (BindingClient): Client for interacting with the Bindings API.
        collection (CollectionClient): Client for interacting with the Collections API.
        document (DocumentClient): Client for interacting with the Documents API.
        index (IndexClient): Client for interacting with the Indexes API.
        transformer (TransformerClient): Client for interacting with the Transformers API.
    """

    base_url: str
    aclient: httpx.AsyncClient
    client: httpx.Client

    binding: BindingClient
    collection: CollectionClient
    document: DocumentClient
    index: IndexClient
    transformer: TransformerClient

    def __init__(self,
                 base_url: str = DEFAULT_BASE_URL,
                 api_timeout: int = API_TIMEOUT,
                 client_kwargs: dict = None,
                 aclient_kwargs: dict = None) -> None:
        """ Initialize a LexyClient instance.

        Args:
            base_url (str, optional): Base URL for the Lexy API. Defaults to DEFAULT_BASE_URL.
            api_timeout (int, optional): Timeout in seconds for API requests. Defaults to API_TIMEOUT.
            client_kwargs (dict, optional): Keyword arguments for the synchronous API client.
            aclient_kwargs (dict, optional): Keyword arguments for the asynchronous API client.
        """
        self.base_url = base_url
        self.api_timeout = api_timeout

        client_kwargs = client_kwargs or {}
        self._client = httpx.Client(base_url=self.base_url, timeout=self.api_timeout, **client_kwargs)
        aclient_kwargs = aclient_kwargs or {}
        self._aclient = httpx.AsyncClient(base_url=self.base_url, timeout=self.api_timeout, **aclient_kwargs)

        # binding
        self.binding = BindingClient(self)
        self.create_binding = self.binding.add_binding
        self.delete_binding = self.binding.delete_binding
        self.get_binding = self.binding.get_binding
        self.list_bindings = self.binding.list_bindings
        self.update_binding = self.binding.update_binding

        # collection
        self.collection = CollectionClient(self)
        self.create_collection = self.collection.add_collection
        self.delete_collection = self.collection.delete_collection
        self.get_collection = self.collection.get_collection
        self.list_collections = self.collection.list_collections
        self.update_collection = self.collection.update_collection

        # document
        self.document = DocumentClient(self)
        self.add_documents = self.document.add_documents
        self.bulk_delete_documents = self.document.bulk_delete_documents
        self.delete_document = self.document.delete_document
        self.get_document = self.document.get_document
        self.list_documents = self.document.list_documents
        self.update_document = self.document.update_document
        self.upload_documents = self.document.upload_documents

        # index
        self.index = IndexClient(self)
        self.create_index = self.index.add_index
        self.delete_index = self.index.delete_index
        self.get_index = self.index.get_index
        self.list_indexes = self.index.list_indexes
        self.query_index = self.index.query_index
        self.update_index = self.index.update_index

        # transformer
        self.transformer = TransformerClient(self)
        self.create_transformer = self.transformer.add_transformer
        self.delete_transformer = self.transformer.delete_transformer
        self.get_transformer = self.transformer.get_transformer
        self.list_transformers = self.transformer.list_transformers
        self.update_transformer = self.transformer.update_transformer
        self.transform_document = self.transformer.transform_document

    @property
    def client(self) -> httpx.Client:
        if self._client is None:
            raise LexyClientError("Client is not set.")
        return self._client

    @client.setter
    def client(self, value) -> None:
        self._client = value

    @property
    def aclient(self) -> httpx.AsyncClient:
        if self._aclient is None:
            raise LexyClientError("AsyncClient is not set.")
        return self._aclient

    @aclient.setter
    def aclient(self, value) -> None:
        self._aclient = value

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

    @property
    def bindings(self):
        """ Get a list of all bindings. """
        return self.binding.list_bindings()

    @property
    def collections(self):
        """ Get a list of all collections. """
        return self.collection.list_collections()

    @property
    def indexes(self):
        """ Get a list of all indexes. """
        return self.index.list_indexes()

    @property
    def transformers(self):
        """ Get a list of all transformers. """
        return self.transformer.list_transformers()

    def info(self):
        """ Print info about the Lexy server. """
        collections_str = "\n".join([f"\t- {c.__repr__()}" for c in self.collections])
        indexes_str = "\n".join([f"\t- {i.__repr__()}" for i in self.indexes])
        transformers_str = "\n".join([f"\t- {t.__repr__()}" for t in self.transformers])
        bindings_str = "\n".join([f"\t- {b.__repr__()}" for b in self.bindings])
        info_str = \
            f"Lexy server <{self.base_url}>\n\n" \
            f"{len(self.collections)} Collections\n{collections_str}\n" \
            f"{len(self.indexes)} Indexes\n{indexes_str}\n" \
            f"{len(self.transformers)} Transformers\n{transformers_str}\n" \
            f"{len(self.bindings)} Bindings\n{bindings_str}\n"
        print(info_str)
