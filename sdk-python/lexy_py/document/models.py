import textwrap
from datetime import datetime
from typing import Any, Optional, TYPE_CHECKING

from pydantic import BaseModel, Field, PrivateAttr

if TYPE_CHECKING:
    from lexy_py.client import LexyClient


class DocumentModel(BaseModel):
    """ Document model """
    document_id: Optional[str] = None
    content: str = Field(..., min_length=1)
    meta: Optional[dict[Any, Any]] = Field(default={})
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    collection_id: Optional[str] = None

    def __repr__(self):
        return f'<Document("{textwrap.shorten(self.content, 100, placeholder="...")}", {self.document_id})>'

    def __init__(self, content: str, **data: Any):
        super().__init__(content=content, **data)


class DocumentCreate(BaseModel):
    """ Document create model """
    content: str = Field(..., min_length=1)
    meta: Optional[dict[Any, Any]] = Field(default={})


class DocumentUpdate(BaseModel):
    """ Document update model """
    content: Optional[str] = None
    meta: Optional[dict[Any, Any]] = None


class Document(DocumentModel):
    __doc__ = DocumentModel.__doc__
    _client: Optional["LexyClient"] = PrivateAttr(default=None)

    def __init__(self, content: str, **data: Any):
        super().__init__(content=content, **data)
        self._client = data.pop('client', None)

    @property
    def client(self) -> "LexyClient":
        if not self._client:
            raise ValueError("API client has not been set.")
        return self._client
