from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import delete, exists, select
from sqlmodel.ext.asyncio.session import AsyncSession

from lexy.db.session import get_session
from lexy.models.collection import Collection, CollectionCreate, CollectionUpdate
from lexy.models.document import Document


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
    # check if collection already exists
    result = await session.execute(select(exists().where(Collection.collection_id == collection.collection_id)))
    existing_result = result.scalar()
    if existing_result:
        raise HTTPException(status_code=400, detail="Collection already exists")

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
async def delete_collection(collection_id: str,
                            delete_documents: bool = False,
                            session: AsyncSession = Depends(get_session)) -> dict:
    result = await session.exec(select(Collection).where(Collection.collection_id == collection_id))
    collection = result.first()

    if not collection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")

    # delete any documents in the collection
    deleted_count = 0
    if delete_documents is True:
        statement = delete(Document).where(Document.collection_id == collection_id)
        result = await session.execute(statement)
        deleted_count = result.rowcount
    else:
        # check if there are any related documents
        statement = select(exists().where(Document.collection_id == collection_id)).select_from(Document)
        result = await session.execute(statement)
        has_documents = result.scalar()
        if has_documents:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="There are still documents in this collection. "
                                       "Set delete_documents=True to delete them.")

    await session.delete(collection)
    await session.commit()
    return {"msg": "Collection deleted", "collection_id": collection_id, "documents_deleted": deleted_count}
