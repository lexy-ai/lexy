from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from lexy.db.session import get_session
from lexy.models.collection import Collection, CollectionCreate, CollectionUpdate


router = APIRouter()


@router.get("/collections",
            response_model=list[Collection],
            status_code=status.HTTP_200_OK,
            name="get_collections",
            description="Get all collections")
async def get_collections(session: AsyncSession = Depends(get_session)) -> list[Collection]:
    result = await session.execute(select(Collection))
    collections = result.scalars().all()
    return collections


@router.post("/collections",
             response_model=Collection,
             status_code=status.HTTP_201_CREATED,
             name="add_collection",
             description="Create a new collection")
async def add_collection(collection: CollectionCreate, session: AsyncSession = Depends(get_session)) -> Collection:
    collection = Collection(**collection.dict())
    session.add(collection)
    await session.commit()
    await session.refresh(collection)
    return collection


@router.get("/collections/{collection_id}",
            response_model=Collection,
            status_code=status.HTTP_200_OK,
            name="get_collection",
            description="Get a collection")
async def get_collection(collection_id: str, session: AsyncSession = Depends(get_session)) -> Collection:
    result = await session.execute(select(Collection).where(Collection.collection_id == collection_id))
    collection = result.scalars().first()
    if not collection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")
    return collection


@router.patch("/collections/{collection_id}",
              response_model=Collection,
              status_code=status.HTTP_200_OK,
              name="update_collection",
              description="Update a collection")
async def update_collection(collection_id: str, collection: CollectionUpdate,
                            session: AsyncSession = Depends(get_session)) -> Collection:
    result = await session.execute(select(Collection).where(Collection.collection_id == collection_id))
    db_collection = result.scalars().first()
    if not db_collection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")
    collection_data = collection.dict(exclude_unset=True)
    for key, value in collection_data.items():
        setattr(db_collection, key, value)
    session.add(db_collection)
    await session.commit()
    await session.refresh(db_collection)
    return db_collection


@router.delete("/collections/{collection_id}",
               status_code=status.HTTP_200_OK,
               name="delete_collection",
               description="Delete a collection")
async def delete_collection(collection_id: str, session: AsyncSession = Depends(get_session)) -> dict:
    result = await session.execute(select(Collection).where(Collection.collection_id == collection_id))
    collection = result.scalars().first()
    if not collection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")
    # TODO: delete all documents in the collection
    # TODO: loop through bindings and set status to "detached"
    await session.delete(collection)
    await session.commit()
    return {"Say": "Collection deleted!"}
