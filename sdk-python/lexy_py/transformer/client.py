"""Client for interacting with the Transformer API."""

from typing import Optional, TYPE_CHECKING

import httpx

from lexy_py.exceptions import handle_response
from .models import Transformer, TransformerUpdate
from lexy_py.document.models import Document

if TYPE_CHECKING:
    from lexy_py.client import LexyClient


class TransformerClient:
    """
    This class is used to interact with the Lexy Transformer API.

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

    def list_transformers(self) -> list[Transformer]:
        """Synchronously get a list of all transformers.

        Returns:
            list[Transformer]: A list of all transformers.
        """
        r = self.client.get("/transformers")
        handle_response(r)
        return [
            Transformer(**transformer, client=self._lexy_client)
            for transformer in r.json()
        ]

    async def alist_transformers(self) -> list[Transformer]:
        """Asynchronously get a list of all transformers.

        Returns:
            list[Transformer]: A list of all transformers.
        """
        r = await self.aclient.get("/transformers")
        handle_response(r)
        return [
            Transformer(**transformer, client=self._lexy_client)
            for transformer in r.json()
        ]

    def get_transformer(self, transformer_id: str) -> Transformer:
        """Synchronously get a transformer.

        Args:
            transformer_id (str): The ID of the transformer to get.

        Returns:
            Transformer: The transformer.
        """
        r = self.client.get(f"/transformers/{transformer_id}")
        handle_response(r)
        return Transformer(**r.json(), client=self._lexy_client)

    async def aget_transformer(self, transformer_id: str) -> Transformer:
        """Asynchronously get a transformer.

        Args:
            transformer_id (str): The ID of the transformer to get.

        Returns:
            Transformer: The transformer.
        """
        r = await self.aclient.get(f"/transformers/{transformer_id}")
        handle_response(r)
        return Transformer(**r.json(), client=self._lexy_client)

    def create_transformer(
        self,
        transformer_id: str,
        *,
        path: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Transformer:
        """Synchronously create a transformer.

        Args:
            transformer_id (str): The ID of the transformer to create.
            path (str, optional): The path of the transformer to create.
            description (str, optional): The description of the transformer to create.

        Returns:
            Transformer: The created transformer.
        """
        transformer = Transformer(
            transformer_id=transformer_id, path=path, description=description
        )
        r = self.client.post("/transformers", json=transformer.model_dump())
        handle_response(r)
        return Transformer(**r.json(), client=self._lexy_client)

    async def acreate_transformer(
        self,
        transformer_id: str,
        *,
        path: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Transformer:
        """Asynchronously create a transformer.

        Args:
            transformer_id (str): The ID of the transformer to create.
            path (str, optional): The path of the transformer to create.
            description (str, optional): The description of the transformer to create.

        Returns:
            Transformer: The created transformer.
        """
        transformer = Transformer(
            transformer_id=transformer_id, path=path, description=description
        )
        r = await self.aclient.post("/transformers", json=transformer.model_dump())
        handle_response(r)
        return Transformer(**r.json(), client=self._lexy_client)

    def update_transformer(
        self,
        transformer_id: str,
        *,
        path: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Transformer:
        """Synchronously update a transformer.

        Args:
            transformer_id (str): The ID of the transformer to update.
            path (str, optional): The updated path of the transformer.
            description (str, optional): The updated description of the transformer.

        Returns:
            Transformer: The updated transformer.
        """
        transformer = TransformerUpdate(path=path, description=description)
        r = self.client.patch(
            f"/transformers/{transformer_id}",
            json=transformer.model_dump(exclude_none=True),
        )
        handle_response(r)
        return Transformer(**r.json(), client=self._lexy_client)

    async def aupdate_transformer(
        self,
        transformer_id: str,
        *,
        path: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Transformer:
        """Asynchronously update a transformer.

        Args:
            transformer_id (str): The ID of the transformer to update.
            path (str, optional): The updated path of the transformer.
            description (str, optional): The updated description of the transformer.

        Returns:
            Transformer: The updated transformer.
        """
        transformer = TransformerUpdate(path=path, description=description)
        r = await self.aclient.patch(
            f"/transformers/{transformer_id}",
            json=transformer.model_dump(exclude_none=True),
        )
        handle_response(r)
        return Transformer(**r.json(), client=self._lexy_client)

    def delete_transformer(self, transformer_id: str) -> dict:
        """Synchronously delete a transformer.

        Args:
            transformer_id (str): The ID of the transformer to delete.
        """
        r = self.client.delete(f"/transformers/{transformer_id}")
        handle_response(r)
        return r.json()

    async def adelete_transformer(self, transformer_id: str) -> dict:
        """Asynchronously delete a transformer.

        Args:
            transformer_id (str): The ID of the transformer to delete.
        """
        r = await self.aclient.delete(f"/transformers/{transformer_id}")
        handle_response(r)
        return r.json()

    def transform_document(
        self,
        transformer_id: str,
        document: Document | dict,
        transformer_params: dict = None,
        content_only: bool = False,
    ) -> dict:
        """Synchronously transform a document.

        Args:
            transformer_id (str): The ID of the transformer to use.
            document (Document | dict): The document to transform.
            transformer_params (dict, optional): The transformer parameters. Defaults to None.
            content_only (bool, optional): Whether to submit only the document content and not the document itself.
                Use this option when the transformer doesn't accept Document objects as inputs. Defaults to False.

        Returns:
            dict: A dictionary containing the generated task ID and the result of the transformer.

        Examples:
            >>> from lexy_py import LexyClient
            >>> lx = LexyClient()
            >>> lx.transformer.transform_document("text.counter.word_counter", {"content": "Hello world!"})
            {'task_id': '65ecd2f7-bac4-4747-9e65-a6d21a72f585', 'result': [2, 'world!']}
        """
        if isinstance(document, dict):
            document = Document(**document)
        data = {"document": document.model_dump(mode="json")}
        if transformer_params:
            data["transformer_params"] = transformer_params
        if content_only:
            data["content_only"] = content_only
        r = self.client.post(f"/transformers/{transformer_id}", json=data)
        handle_response(r)
        return r.json()
