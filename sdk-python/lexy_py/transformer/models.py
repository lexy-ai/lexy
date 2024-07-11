from datetime import datetime
from typing import Any, Optional, TYPE_CHECKING

from pydantic import BaseModel, Field, PrivateAttr

from lexy_py.document.models import Document

if TYPE_CHECKING:
    from lexy_py.client import LexyClient


class TransformerModel(BaseModel):
    """Transformer model"""

    transformer_id: str = Field(
        ..., min_length=1, max_length=255, pattern=r"^[a-zA-Z][a-zA-Z0-9_.-]+$"
    )
    path: Optional[str] = Field(
        default=None, min_length=1, max_length=255, pattern=r"^[a-zA-Z][a-zA-Z0-9_.]+$"
    )
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __repr__(self):
        return (
            f"<Transformer('{self.transformer_id}', description='{self.description}')>"
        )


class TransformerUpdate(BaseModel):
    """Transformer update model"""

    path: Optional[str] = None
    description: Optional[str] = None


class Transformer(TransformerModel):
    __doc__ = TransformerModel.__doc__
    _client: Optional["LexyClient"] = PrivateAttr(default=None)

    def __init__(self, **data: Any):
        super().__init__(**data)
        self._client = data.pop("client", None)

    @property
    def client(self) -> "LexyClient":
        if not self._client:
            raise ValueError("API client has not been set.")
        return self._client

    def transform_document(
        self,
        document: Document | dict,
        transformer_params: dict = None,
        content_only: bool = False,
    ) -> dict:
        """Synchronously transform a document.

        Args:
            document (Document | dict): The document to transform.
            transformer_params (dict, optional): The transformer parameters. Defaults
                to None.
            content_only (bool, optional): Whether to submit only the document content
                and not the document itself. Use this option when the transformer
                doesn't accept Document objects as inputs. Defaults to False.

        Returns:
            dict: A dictionary containing the generated task ID and the result of the
                transformer.

        Examples:
            >>> from lexy_py import LexyClient
            >>> lx = LexyClient()
            >>> minilm = lx.get_transformer('text.embeddings.minilm')
            >>> minilm.transform_document({'content': 'Good morning!'})
            {'task_id': '449d9d79-4a57-4191-95d3-9c38955c8ced',
             'result': [-0.03085244633257389, 0.028894789516925812, ...]}
        """
        return self.client.transformer.transform_document(
            transformer_id=self.transformer_id,
            document=document,
            transformer_params=transformer_params,
            content_only=content_only,
        )
