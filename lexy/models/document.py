import base64
from datetime import datetime
from io import BytesIO
from typing import Any, Optional, TYPE_CHECKING
from uuid import uuid4, UUID

import httpx
from PIL import Image
from pydantic import PrivateAttr
from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel, Relationship

from lexy.models.collection import Collection
from lexy.storage import presigned_url_is_expired
from lexy.storage.client import generate_presigned_urls_for_document

if TYPE_CHECKING:
    import boto3


class DocumentBase(SQLModel):
    content: str
    meta: Optional[dict[Any, Any]] = Field(sa_column=Column(JSONB), default={})
    _image: Optional["Image"] = PrivateAttr(default=None)

    # TODO: this __init__ is only needed because SQLModel is missing `_init_private_attributes` - should no longer be
    #  needed after updating to Pydantic v2. Sources:
    #  - https://github.com/tiangolo/sqlmodel/pull/472#issuecomment-1301647570
    #  - https://github.com/tiangolo/sqlmodel/issues/504
    def __init__(self, **data: Any):
        super().__init__(**data)
        self._image = None

    @property
    def image(self) -> Image:
        if not self._image:
            self._image = self.meta.get('image', {}).get('im')
        if not self._image:
            base64_str = self.meta.get('image', {}).get('base64')
            if base64_str:
                self._image = self.image_from_base64_str(base64_str)
        if not self._image:
            if self.object_url:
                self._image = self.image_from_url(self.object_url)
        return self._image

    @property
    def object_url(self) -> Optional[str]:
        if not self.meta.get('_urls'):
            self.refresh_object_urls()
        url = self.meta.get('_urls', {}).get('object')
        # check if url is expired and refresh if needed
        if url and presigned_url_is_expired(url):
            self.refresh_object_urls()
            url = self.meta.get('_urls', {}).get('object')
        return url

    def refresh_object_urls(self,
                            s3_client: "boto3.client" = None,
                            expiration: int = 3600) -> None:
        urls = generate_presigned_urls_for_document(self, s3_client=s3_client, expiration=expiration)
        self.meta['_urls'] = urls

    # TODO: move to future ImageDocument class
    @staticmethod
    def image_from_base64_str(base64_str: str) -> Image:
        img_bytes = base64.b64decode(base64_str)
        return Image.open(BytesIO(img_bytes))

    # TODO: move to future ImageDocument class
    @staticmethod
    def image_from_url(url: str) -> Image:
        r = httpx.get(url)
        return Image.open(BytesIO(r.content))


class Document(DocumentBase, table=True):
    __tablename__ = "documents"
    document_id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()),
    )
    collection_id: str = Field(default="default", foreign_key="collections.collection_id")
    collection: Collection = Relationship(back_populates="documents", sa_relationship_kwargs={'lazy': 'selectin'})
    embeddings: list["Embedding"] = Relationship(back_populates="document")


class DocumentCreate(DocumentBase):
    pass


class DocumentUpdate(DocumentBase):
    content: Optional[str] = None
    meta: Optional[dict[Any, Any]] = None


# class DocumentInDB(DocumentBase):
#     pass
