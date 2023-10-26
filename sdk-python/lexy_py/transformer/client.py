""" Client for interacting with the Transformer API. """

from typing import Optional

import httpx

from .models import Transformer, TransformerUpdate


class TransformerClient:
    """
    This class is used to interact with the Lexy Transformer API.

    Attributes:
        aclient (httpx.AsyncClient): Asynchronous API client.
        client (httpx.Client): Synchronous API client.
    """

    def __init__(self, aclient: httpx.AsyncClient, client: httpx.Client) -> None:
        self.aclient = aclient
        self.client = client

    def list_transformers(self) -> list[Transformer]:
        """ Synchronously get a list of all transformers.

        Returns:
            list[Transformer]: A list of all transformers.
        """
        r = self.client.get("/transformers")
        return [Transformer(**transformer) for transformer in r.json()]

    async def alist_transformers(self) -> list[Transformer]:
        """ Asynchronously get a list of all transformers.

        Returns:
            list[Transformer]: A list of all transformers.
        """
        r = await self.aclient.get("/transformers")
        return [Transformer(**transformer) for transformer in r.json()]

    def get_transformer(self, transformer_id: str) -> Transformer:
        """ Synchronously get a transformer.

        Args:
            transformer_id (str): The ID of the transformer to get.

        Returns:
            Transformer: The transformer.
        """
        r = self.client.get(f"/transformers/{transformer_id}")
        return Transformer(**r.json())

    async def aget_transformer(self, transformer_id: str) -> Transformer:
        """ Asynchronously get a transformer.

        Args:
            transformer_id (str): The ID of the transformer to get.

        Returns:
            Transformer: The transformer.
        """
        r = await self.aclient.get(f"/transformers/{transformer_id}")
        return Transformer(**r.json())

    def add_transformer(self, transformer_id: str, path: str, description: Optional[str] = None) -> Transformer:
        """ Synchronously add a transformer.

        Args:
            transformer_id (str): The ID of the transformer to add.
            path (str): The path of the transformer to add.
            description (str, optional): The description of the transformer to add.

        Returns:
            Transformer: The added transformer.
        """
        data = {"transformer_id": transformer_id, "path": path}
        if description:
            data["description"] = description
        r = self.client.post("/transformers", json=data)
        return Transformer(**r.json())

    async def aadd_transformer(self, transformer_id: str, path: str, description: Optional[str] = None) -> Transformer:
        """ Asynchronously add a transformer.

        Args:
            transformer_id (str): The ID of the transformer to add.
            path (str): The path of the transformer to add.
            description (str, optional): The description of the transformer to add.

        Returns:
            Transformer: The added transformer.
        """
        data = {"transformer_id": transformer_id, "path": path}
        if description:
            data["description"] = description
        r = await self.aclient.post("/transformers", json=data)
        return Transformer(**r.json())

    def update_transformer(self, transformer_id: str, path: Optional[str] = None,
                           description: Optional[str] = None) -> Transformer:
        """ Synchronously update a transformer.

        Args:
            transformer_id (str): The ID of the transformer to update.
            path (str, optional): The updated path of the transformer.
            description (str, optional): The updated description of the transformer.

        Returns:
            Transformer: The updated transformer.
        """
        transformer = TransformerUpdate(path=path, description=description)
        r = self.client.patch(f"/transformers/{transformer_id}", json=transformer.dict(exclude_none=True))
        return Transformer(**r.json())

    async def aupdate_transformer(self, transformer_id: str, path: Optional[str] = None,
                                    description: Optional[str] = None) -> Transformer:
        """ Asynchronously update a transformer.

        Args:
            transformer_id (str): The ID of the transformer to update.
            path (str, optional): The updated path of the transformer.
            description (str, optional): The updated description of the transformer.

        Returns:
            Transformer: The updated transformer.
        """
        transformer = TransformerUpdate(path=path, description=description)
        r = await self.aclient.patch(f"/transformers/{transformer_id}", json=transformer.dict(exclude_none=True))
        return Transformer(**r.json())

    def delete_transformer(self, transformer_id: str) -> dict:
        """ Synchronously delete a transformer.

        Args:
            transformer_id (str): The ID of the transformer to delete.
        """
        r = self.client.delete(f"/transformers/{transformer_id}")
        return r.json()

    async def adelete_transformer(self, transformer_id: str) -> dict:
        """ Asynchronously delete a transformer.

        Args:
            transformer_id (str): The ID of the transformer to delete.
        """
        r = await self.aclient.delete(f"/transformers/{transformer_id}")
        return r.json()
