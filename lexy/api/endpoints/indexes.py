import logging
import time

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from lexy.db.session import get_session
from lexy.models.index import Index, IndexCreate, IndexUpdate
from lexy.core.events import restart_celery_worker
from lexy.api.deps import index_manager


logger = logging.getLogger(__name__)
router = APIRouter()

# TODO: move this to the proper config location
celery_db_worker = 'celery@celeryworker'


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
    # check if index already exists
    result = await session.execute(select(Index).where(Index.index_id == index.index_id))
    existing_index = result.scalars().first()
    if existing_index:
        raise HTTPException(status_code=400, detail="Index already exists")

    # create new index
    index = Index(**index.dict())
    session.add(index)
    await session.commit()
    await session.refresh(index)

    # create the index model and table
    _ = index_manager.create_index_model_and_table(index_id=index.index_id)
    logger.info(f"Restarting db worker '{celery_db_worker}' following creation of index table "
                f"for index_id: {index.index_id}")
    time.sleep(0.5)
    celery_restart_response = restart_celery_worker(celery_db_worker)
    logger.info(f"{celery_restart_response = }")

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
async def delete_index(index_id: str,
                       drop_table: bool = False,
                       session: AsyncSession = Depends(get_session)) -> dict:
    result = await session.execute(select(Index).where(Index.index_id == index_id))
    index = result.scalars().first()
    if not index:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Index not found")

    index_table_name = index.index_table_name

    # NOTE: Deleting the index with option `drop_table=False` will leave the index model in the index manager.
    #   To remove it, recreate the index, and then delete with `drop_table=True`. The issue with removing it from the
    #   index manager is created when trying to recreate a table with the same name.
    table_dropped = False
    if drop_table:
        table_dropped = index_manager.drop_index_table(index_id=index_id)

    await session.delete(index)
    await session.commit()

    # TODO: restart celery worker here?
    return {"msg": "Index deleted",
            "index_id": index_id,
            "index_table_name": index_table_name,
            "table_dropped": table_dropped}
