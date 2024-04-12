"""Module for CRUD helpers."""

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from lexy.models import Collection, Document


async def get_collection_by_id(*, session: AsyncSession, collection_id: str) -> Collection | None:
    """Get a collection by id."""
    result = await session.exec(
        select(Collection).where(Collection.collection_id == collection_id)
    )
    collection = result.first()
    return collection


async def get_collection_by_name(*, session: AsyncSession, collection_name: str) -> Collection | None:
    """Get a collection by name."""
    result = await session.exec(
        select(Collection).where(Collection.collection_name == collection_name)
    )
    collection = result.first()
    return collection


async def get_document_by_id(*, session: AsyncSession, document_id: str) -> Document | None:
    """Get a document by id."""
    result = await session.exec(
        select(Document).where(Document.document_id == document_id)
    )
    document = result.first()
    return document


async def get_documents_by_collection_id(*, session: AsyncSession, collection_id: str) -> list[Document]:
    """Get all documents in a collection."""
    result = await session.exec(
        select(Document).where(Document.collection_id == collection_id)
    )
    documents = result.all()
    return documents


async def get_documents_by_collection_id_and_content(*, session: AsyncSession, collection_id: str, content: str) \
        -> list[Document]:
    """Get all documents in a collection with a specific value for `content`."""
    result = await session.exec(
        select(Document).where(Document.collection_id == collection_id).where(Document.content == content)
    )
    documents = result.all()
    return documents
