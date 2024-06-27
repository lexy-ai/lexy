import base64
import textwrap
from datetime import datetime
from io import BytesIO
from typing import Any, Optional, TYPE_CHECKING

from PIL import Image
from pydantic import BaseModel, Field, PrivateAttr

from lexy_py.storage import presigned_url_is_expired

if TYPE_CHECKING:
    from lexy_py.client import LexyClient


class DocumentModel(BaseModel):
    """Document model"""

    document_id: Optional[str] = None
    content: str = Field(...)
    meta: Optional[dict[Any, Any]] = Field(default={})
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    collection_id: Optional[str] = None

    def __repr__(self):
        return f'<Document("{textwrap.shorten(self.content, 100, placeholder="...")}")>'

    def __init__(self, content: str, **data: Any):
        super().__init__(content=content, **data)


class DocumentCreate(BaseModel):
    """Document create model"""

    content: str = Field(...)
    meta: Optional[dict[Any, Any]] = Field(default={})


class DocumentUpdate(BaseModel):
    """Document update model"""

    content: Optional[str] = None
    meta: Optional[dict[Any, Any]] = None


class Document(DocumentModel):
    __doc__ = DocumentModel.__doc__
    _client: Optional["LexyClient"] = PrivateAttr(default=None)
    _image: Optional["Image"] = PrivateAttr(default=None)
    _urls: Optional[dict] = PrivateAttr(default=None)

    def __init__(self, content: str, **data: Any):
        super().__init__(content=content, **data)
        self._client = data.pop("client", None)

    @property
    def client(self) -> "LexyClient":
        if not self._client:
            raise ValueError("API client has not been set.")
        return self._client

    @property
    def image(self) -> Image:
        if not self._image:
            self._image = self.meta.get("image", {}).get("im")
        if not self._image:
            base64_str = self.meta.get("image", {}).get("base64")
            if base64_str:
                self._image = self.image_from_base64_str(base64_str)
        if not self._image:
            if self.object_url:
                self._image = self.image_from_url(self.object_url)
        return self._image

    @property
    def object_url(self) -> str | None:
        if self._urls is None:
            self._refresh_urls()
        url = self._urls.get("object", None)
        # check if url is expired and refresh if needed
        storage_service = self.meta.get("storage_service")
        if url and presigned_url_is_expired(url, storage_service=storage_service):
            self._refresh_urls()
            url = self._urls.get("object", None)
        return url

    def get_thumbnail_url(
        self, size: tuple[int, int] = (200, 200), refresh: bool = False
    ) -> str | None:
        if self._urls is None or refresh:
            self._refresh_urls()
        url = self._urls.get("thumbnails", {}).get(f"{size[0]}x{size[1]}")
        # if that size doesn't exist, get any size
        if not url:
            url = next(iter(self._urls.get("thumbnails", {}).values()), None)
        # check if url is expired and refresh if needed
        storage_service = (
            self.meta.get("image", {})
            .get("thumbnails", {})
            .get(f"{size[0]}x{size[1]}", {})
            .get("storage_service")
        )
        if url and presigned_url_is_expired(url, storage_service=storage_service):
            return self.get_thumbnail_url(size, refresh=True)
        return url

    thumbnail_url = property(get_thumbnail_url)

    def _refresh_urls(self):
        self._urls = self.client.document.get_document_urls(self.document_id)

    # TODO: move to future ImageDocument class
    def image_from_url(self, url: str) -> Image:
        if self._client:
            r = self.client.get(url)
        else:
            import httpx

            r = httpx.get(url)
        return Image.open(BytesIO(r.content))

    # TODO: move to future ImageDocument class
    @staticmethod
    def image_from_base64_str(base64_str: str) -> Image:
        img_bytes = base64.b64decode(base64_str)
        return Image.open(BytesIO(img_bytes))
