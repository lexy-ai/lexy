"""Module for CRUD helpers."""

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from lexy.models import Collection


async def get_collection_by_id(*, session: AsyncSession, collection_id: str) -> Collection | None:
    """Get a collection by id."""
    result = await session.exec(
        select(Collection).where(Collection.uid == collection_id)
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
