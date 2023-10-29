from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from lexy.db.session import get_session
from lexy.models.index import Index, IndexCreate, IndexUpdate
from lexy.core.events import create_new_index_table


router = APIRouter()


@router.get("/indexes",
            response_model=list[Index],
            status_code=status.HTTP_200_OK,
            name="get_indexes",
            description="Get all indexes")
async def get_indexes(session: AsyncSession = Depends(get_session)) -> list[Index]:
    result = await session.execute(select(Index))
    indexes = result.scalars().all()
    return indexes


@router.post("/indexes",
             status_code=status.HTTP_201_CREATED,
             name="add_index",
             description="Create a new index")
async def add_index(index: IndexCreate, session: AsyncSession = Depends(get_session)) -> Index:
    index = Index(**index.dict())
    session.add(index)
    await session.commit()
    await session.refresh(index)
    create_new_index_table(index_id=index.index_id)
    return index


@router.get("/indexes/{index_id}",
            response_model=Index,
            status_code=status.HTTP_200_OK,
            name="get_index",
            description="Get an index")
async def get_index(index_id: str, session: AsyncSession = Depends(get_session)) -> Index:
    result = await session.execute(select(Index).where(Index.index_id == index_id))
    index = result.scalars().first()
    if not index:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Index not found")
    return index


@router.patch("/indexes/{index_id}",
              response_model=Index,
              status_code=status.HTTP_200_OK,
              name="update_index",
              description="Update an index")
async def update_index(index_id: str, index: IndexUpdate,
                       session: AsyncSession = Depends(get_session)) -> Index:
    result = await session.execute(select(Index).where(Index.index_id == index_id))
    db_index = result.scalars().first()
    if not db_index:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Index not found")
    index_data = index.dict(exclude_unset=True)
    for key, value in index_data.items():
        setattr(db_index, key, value)
    session.add(db_index)
    await session.commit()
    await session.refresh(db_index)
    return db_index


@router.delete("/indexes/{index_id}",
               status_code=status.HTTP_200_OK,
               name="delete_index",
               description="Delete an index")
async def delete_index(index_id: str, session: AsyncSession = Depends(get_session)) -> dict:
    result = await session.execute(select(Index).where(Index.index_id == index_id))
    index = result.scalars().first()
    if not index:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Index not found")
    await session.delete(index)
    await session.commit()
    return {"Say": "Index deleted!"}
