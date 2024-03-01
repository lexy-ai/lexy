""" Client for interacting with the Bindings API. """

from typing import Optional, TYPE_CHECKING

import httpx

from lexy_py.exceptions import handle_response
from lexy_py.filters import FilterBuilder
from .models import Binding, BindingCreate, BindingUpdate

if TYPE_CHECKING:
    from lexy_py.client import LexyClient


class BindingClient:
    """
    This class is used to interact with the Lexy Bindings API.

    Properties:
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

    def list_bindings(self) -> list[Binding]:
        """ Synchronously get a list of all bindings.

        Returns:
            list[Binding]: A list of all bindings.
        """
        r = self.client.get("/bindings")
        handle_response(r)
        return [Binding(**binding, client=self._lexy_client) for binding in r.json()]

    async def alist_bindings(self) -> list[Binding]:
        """ Asynchronously get a list of all bindings.

        Returns:
            list[Binding]: A list of all bindings.
        """
        r = await self.aclient.get("/bindings")
        handle_response(r)
        return [Binding(**binding, client=self._lexy_client) for binding in r.json()]

    def add_binding(self,
                    collection_id: str,
                    transformer_id: str,
                    index_id: str,
                    description: Optional[str] = None,
                    execution_params: Optional[dict] = None,
                    transformer_params: Optional[dict] = None,
                    filters: Optional[dict | FilterBuilder] = None,
                    status: Optional[str] = None) -> Binding:
        """ Synchronously add a new binding.

        Args:
            collection_id (str): The ID of the collection containing the source documents.
            transformer_id (str): The ID of the transformer that the binding will run.
            index_id (str): The ID of the index in which the binding will store its output.
            description (str, optional): A description of the binding.
            execution_params (dict, optional): Parameters to pass to the binding's execution function.
            transformer_params (dict, optional): Parameters to pass to the transformer.
            filters (dict | FilterBuilder, optional): Filters to apply to documents in the collection before running
                the transformer.
            status (str, optional): The status of the binding. Defaults to "pending".

        Returns:
            Binding: The created binding.

        Examples:
            Create a binding that runs the transformer with ID "image.embeddings.clip" on all image documents in
            the collection with ID "my_collection" and stores the output in the index with ID "image_embeddings".

            >>> from lexy_py import LexyClient, FilterBuilder
            >>> lexy = LexyClient()
            >>> image_filter = FilterBuilder().include("meta.type", "equals", "image")
            >>> binding = lexy.create_binding(collection_id="my_collection",
            ...                               transformer_id="image.embeddings.clip",
            ...                               index_id="image_embeddings",
            ...                               filters=image_filter)
        """
        if execution_params is None:
            execution_params = {}
        if transformer_params is None:
            transformer_params = {}
        if isinstance(filters, FilterBuilder):
            filters = filters.to_dict()
        binding = BindingCreate(
            collection_id=collection_id,
            transformer_id=transformer_id,
            index_id=index_id,
            description=description,
            execution_params=execution_params,
            transformer_params=transformer_params,
            filter=filters,
            status=status
        )
        r = self.client.post("/bindings", json=binding.dict(exclude_none=True))
        handle_response(r)
        return Binding(**r.json()["binding"], client=self._lexy_client)

    async def aadd_binding(self,
                           collection_id: str,
                           transformer_id: str,
                           index_id: str,
                           description: Optional[str] = None,
                           execution_params: Optional[dict] = None,
                           transformer_params: Optional[dict] = None,
                           filters: Optional[dict | FilterBuilder] = None,
                           status: Optional[str] = None) -> Binding:
        """ Asynchronously add a new binding.

        Args:
            collection_id (str): The ID of the collection containing the source documents.
            transformer_id (str): The ID of the transformer that the binding will run.
            index_id (str): The ID of the index in which the binding will store its output.
            description (str, optional): A description of the binding.
            execution_params (dict, optional): Parameters to pass to the binding's execution function.
            transformer_params (dict, optional): Parameters to pass to the transformer.
            filters (dict | FilterBuilder, optional): Filters to apply to documents in the collection before running
                the transformer.
            status (str, optional): The status of the binding. Defaults to "pending".

        Returns:
            Binding: The created binding.
        """
        if execution_params is None:
            execution_params = {}
        if transformer_params is None:
            transformer_params = {}
        if isinstance(filters, FilterBuilder):
            filters = filters.to_dict()
        binding = BindingCreate(
            collection_id=collection_id,
            transformer_id=transformer_id,
            index_id=index_id,
            description=description,
            execution_params=execution_params,
            transformer_params=transformer_params,
            filter=filters,
            status=status
        )
        r = await self.aclient.post("/bindings", json=binding.dict(exclude_none=True))
        handle_response(r)
        return Binding(**r.json()["binding"], client=self._lexy_client)

    def get_binding(self, binding_id: int) -> Binding:
        """ Synchronously get a binding.

        Args:
            binding_id (int): The ID of the binding to get.

        Returns:
            Binding: The binding.
        """
        r = self.client.get(f"/bindings/{binding_id}")
        handle_response(r)
        return Binding(**r.json(), client=self._lexy_client)

    async def aget_binding(self, binding_id: int) -> Binding:
        """ Asynchronously get a binding.

        Args:
            binding_id (int): The ID of the binding to get.

        Returns:
            Binding: The binding.
        """
        r = await self.aclient.get(f"/bindings/{binding_id}")
        handle_response(r)
        return Binding(**r.json(), client=self._lexy_client)

    def update_binding(self,
                       binding_id: int,
                       description: Optional[str] = None,
                       execution_params: Optional[dict] = None,
                       transformer_params: Optional[dict] = None,
                       filters: Optional[dict | FilterBuilder] = None,
                       status: Optional[str] = None) -> Binding:
        """ Synchronously update a binding.

        Args:
            binding_id (int): The ID of the binding to update.
            description (str, optional): A description of the binding.
            execution_params (dict, optional): Parameters to pass to the binding's execution function.
            transformer_params (dict, optional): Parameters to pass to the transformer.
            filters (dict | FilterBuilder, optional): Filters to apply to documents in the collection before running
                the transformer. Set to an empty dict to remove any existing filter.
            status (str, optional): The status of the binding.

        Returns:
            Binding: The updated binding.
        """
        if isinstance(filters, FilterBuilder):
            filters = filters.to_dict()
        binding = BindingUpdate(
            description=description,
            execution_params=execution_params,
            transformer_params=transformer_params,
            filter=filters,
            status=status
        )
        json_payload = binding.dict(exclude_none=True)
        if json_payload["filter"] == {}:  # explicitly removed filters
            json_payload["filter"] = None
        r = self.client.patch(f"/bindings/{binding_id}", json=json_payload)
        handle_response(r)
        return Binding(**r.json(), client=self._lexy_client)

    async def aupdate_binding(self,
                              binding_id: int,
                              description: Optional[str] = None,
                              execution_params: Optional[dict] = None,
                              transformer_params: Optional[dict] = None,
                              filters: Optional[dict | FilterBuilder] = None,
                              status: Optional[str] = None) -> Binding:
        """ Asynchronously update a binding.

        Args:
            binding_id (int): The ID of the binding to update.
            description (str, optional): A description of the binding.
            execution_params (dict, optional): Parameters to pass to the binding's execution function.
            transformer_params (dict, optional): Parameters to pass to the transformer.
            filters (dict | FilterBuilder, optional): Filters to apply to documents in the collection before running
                the transformer. Set to an empty dict to remove any existing filter.
            status (str, optional): The status of the binding.

        Returns:
            Binding: The updated binding.
        """
        if isinstance(filters, FilterBuilder):
            filters = filters.to_dict()
        binding = BindingUpdate(
            description=description,
            execution_params=execution_params,
            transformer_params=transformer_params,
            filter=filters,
            status=status
        )
        json_payload = binding.dict(exclude_none=True)
        if json_payload["filter"] == {}:  # explicitly removed filters
            json_payload["filter"] = None
        r = await self.aclient.patch(f"/bindings/{binding_id}", json=json_payload)
        handle_response(r)
        return Binding(**r.json(), client=self._lexy_client)

    def delete_binding(self, binding_id: int) -> dict:
        """ Synchronously delete a binding.

        Args:
            binding_id (int): The ID of the binding to delete.
        """
        r = self.client.delete(f"/bindings/{binding_id}")
        handle_response(r)
        return r.json()

    async def adelete_binding(self, binding_id: int) -> dict:
        """ Asynchronously delete a binding.

        Args:
            binding_id (int): The ID of the binding to delete.
        """
        r = await self.aclient.delete(f"/bindings/{binding_id}")
        handle_response(r)
        return r.json()
