""" Client for interacting with the Bindings API. """

from typing import Optional

import httpx

from .models import TransformerIndexBinding, TransformerIndexBindingUpdate


class BindingClient:
    """
    This class is used to interact with the Lexy Bindings API.

    Attributes:
        aclient (httpx.AsyncClient): Asynchronous API client.
        client (httpx.Client): Synchronous API client.
    """

    def __init__(self, aclient: httpx.AsyncClient, client: httpx.Client) -> None:
        self.aclient = aclient
        self.client = client

    def list_bindings(self) -> list[TransformerIndexBinding]:
        """ Synchronously get a list of all bindings.

        Returns:
            list[TransformerIndexBinding]: A list of all bindings.
        """
        r = self.client.get("/bindings")
        return [TransformerIndexBinding(**binding) for binding in r.json()]

    async def alist_bindings(self) -> list[TransformerIndexBinding]:
        """ Asynchronously get a list of all bindings.

        Returns:
            list[TransformerIndexBinding]: A list of all bindings.
        """
        r = await self.aclient.get("/bindings")
        return [TransformerIndexBinding(**binding) for binding in r.json()]

    def add_binding(self, collection_id: str, transformer_id: str, index_id: str, description: Optional[str] = None,
                    execution_params: Optional[dict] = None, transformer_params: Optional[dict] = None,
                    filters: Optional[dict] = None, status: Optional[str] = None) -> TransformerIndexBinding:
        """ Synchronously add a new binding.

        Args:
            collection_id (str): The ID of the collection containing the source documents.
            transformer_id (str): The ID of the transformer that the binding will run.
            index_id (str): The ID of the index in which the binding will store its output.
            description (str, optional): A description of the binding.
            execution_params (dict, optional): Parameters to pass to the binding's execution function.
            transformer_params (dict, optional): Parameters to pass to the transformer.
            filters (dict, optional): Filters to apply to documents in the collection before running the transformer.
            status (str, optional): The status of the binding. Defaults to "pending".

        Returns:
            TransformerIndexBinding: The created binding.
        """
        if execution_params is None:
            execution_params = {}
        if transformer_params is None:
            transformer_params = {}
        if filters is None:
            filters = {}
        binding = TransformerIndexBinding(
            collection_id=collection_id,
            transformer_id=transformer_id,
            index_id=index_id,
            description=description,
            execution_params=execution_params,
            transformer_params=transformer_params,
            filters=filters,
            status=status
        )
        r = self.client.post("/bindings", json=binding.dict(exclude_none=True))
        return TransformerIndexBinding(**r.json())

    async def aadd_binding(self, collection_id: str, transformer_id: str, index_id: str,
                           description: Optional[str] = None, execution_params: Optional[dict] = None,
                           transformer_params: Optional[dict] = None, filters: Optional[dict] = None,
                           status: Optional[str] = None) -> TransformerIndexBinding:
        """ Asynchronously add a new binding.

        Args:
            collection_id (str): The ID of the collection containing the source documents.
            transformer_id (str): The ID of the transformer that the binding will run.
            index_id (str): The ID of the index in which the binding will store its output.
            description (str, optional): A description of the binding.
            execution_params (dict, optional): Parameters to pass to the binding's execution function.
            transformer_params (dict, optional): Parameters to pass to the transformer.
            filters (dict, optional): Filters to apply to documents in the collection before running the transformer.
            status (str, optional): The status of the binding. Defaults to "pending".

        Returns:
            TransformerIndexBinding: The created binding.
        """
        if execution_params is None:
            execution_params = {}
        if transformer_params is None:
            transformer_params = {}
        if filters is None:
            filters = {}
        binding = TransformerIndexBinding(
            collection_id=collection_id,
            transformer_id=transformer_id,
            index_id=index_id,
            description=description,
            execution_params=execution_params,
            transformer_params=transformer_params,
            filters=filters,
            status=status
        )
        r = await self.aclient.post("/bindings", json=binding.dict(exclude_none=True))
        return TransformerIndexBinding(**r.json())

    def get_binding(self, binding_id: int) -> TransformerIndexBinding:
        """ Synchronously get a binding.

        Args:
            binding_id (int): The ID of the binding to get.

        Returns:
            TransformerIndexBinding: The binding.
        """
        r = self.client.get(f"/bindings/{binding_id}")
        return TransformerIndexBinding(**r.json())

    async def aget_binding(self, binding_id: int) -> TransformerIndexBinding:
        """ Asynchronously get a binding.

        Args:
            binding_id (int): The ID of the binding to get.

        Returns:
            TransformerIndexBinding: The binding.
        """
        r = await self.aclient.get(f"/bindings/{binding_id}")
        return TransformerIndexBinding(**r.json())

    def update_binding(self, binding_id: int, description: Optional[str] = None,
                       execution_params: Optional[dict] = None, transformer_params: Optional[dict] = None,
                       filters: Optional[dict] = None, status: Optional[str] = None) -> TransformerIndexBinding:
        """ Synchronously update a binding.

        Args:
            binding_id (int): The ID of the binding to update.
            description (str, optional): A description of the binding.
            execution_params (dict, optional): Parameters to pass to the binding's execution function.
            transformer_params (dict, optional): Parameters to pass to the transformer.
            filters (dict, optional): Filters to apply to documents in the collection before running the transformer.
            status (str, optional): The status of the binding.

        Returns:
            TransformerIndexBinding: The updated binding.
        """
        binding = TransformerIndexBindingUpdate(
            description=description,
            execution_params=execution_params,
            transformer_params=transformer_params,
            filters=filters,
            status=status
        )
        r = self.client.patch(f"/bindings/{binding_id}", json=binding.dict(exclude_none=True))
        return TransformerIndexBinding(**r.json())

    async def aupdate_binding(self, binding_id: int, description: Optional[str] = None,
                              execution_params: Optional[dict] = None, transformer_params: Optional[dict] = None,
                              filters: Optional[dict] = None, status: Optional[str] = None) -> TransformerIndexBinding:
        """ Asynchronously update a binding.

        Args:
            binding_id (int): The ID of the binding to update.
            description (str, optional): A description of the binding.
            execution_params (dict, optional): Parameters to pass to the binding's execution function.
            transformer_params (dict, optional): Parameters to pass to the transformer.
            filters (dict, optional): Filters to apply to documents in the collection before running the transformer.
            status (str, optional): The status of the binding.

        Returns:
            TransformerIndexBinding: The updated binding.
        """
        binding = TransformerIndexBindingUpdate(
            description=description,
            execution_params=execution_params,
            transformer_params=transformer_params,
            filters=filters,
            status=status
        )
        r = await self.aclient.patch(f"/bindings/{binding_id}", json=binding.dict(exclude_none=True))
        return TransformerIndexBinding(**r.json())

    def delete_binding(self, binding_id: int) -> dict:
        """ Synchronously delete a binding.

        Args:
            binding_id (int): The ID of the binding to delete.
        """
        r = self.client.delete(f"/bindings/{binding_id}")
        return r.json()

    async def adelete_binding(self, binding_id: int) -> dict:
        """ Asynchronously delete a binding.

        Args:
            binding_id (int): The ID of the binding to delete.
        """
        r = await self.aclient.delete(f"/bindings/{binding_id}")
        return r.json()
