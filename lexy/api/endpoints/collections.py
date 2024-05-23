from io import BytesIO
from typing import Union

from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile
from PIL import Image
from sqlmodel import delete, exists, select
from sqlmodel.ext.asyncio.session import AsyncSession

from lexy import crud
from lexy.db.session import get_session
from lexy.storage.client import (
    construct_key_for_document,
    construct_key_for_thumbnail,
    get_storage_client,
    StorageClient
)
from lexy.models.collection import Collection, CollectionCreate, CollectionUpdate
from lexy.models.document import Document, DocumentCreate
from lexy.core.config import settings
from lexy.core.events import generate_tasks_for_document


router = APIRouter()


@router.get("/collections",
            response_model=Union[Collection, list[Collection]],
            status_code=status.HTTP_200_OK,
            name="get_collections",
            description="Get collections")
async def get_collections(collection_name: str | None = None,
                          session: AsyncSession = Depends(get_session)) -> Collection | list[Collection]:
    if collection_name:
        collection = await crud.get_collection_by_name(session=session, collection_name=collection_name)
        if not collection:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")
        return collection
    result = await session.exec(select(Collection))
    collections = result.all()
    return collections


@router.post("/collections",
             response_model=Collection,
             status_code=status.HTTP_201_CREATED,
             name="add_collection",
             description="Create a new collection")
async def add_collection(collection: CollectionCreate,
                         session: AsyncSession = Depends(get_session)) -> Collection:
    # check if collection with that name already exists
    existing_collection = await crud.get_collection_by_name(
        session=session, collection_name=collection.collection_name
    )
    if existing_collection:
        raise HTTPException(status_code=400, detail="Collection with that name already exists")

    db_collection = Collection.model_validate(collection)
    session.add(db_collection)
    await session.commit()
    await session.refresh(db_collection)
    return db_collection


@router.delete("/collections",
               status_code=status.HTTP_200_OK,
               name="delete_collection_by_name",
               description="Delete a collection by name")
async def delete_collection_by_name(collection_name: str,
                                    delete_documents: bool = False,
                                    session: AsyncSession = Depends(get_session)) -> dict:
    # get the collection
    collection = await crud.get_collection_by_name(session=session, collection_name=collection_name)
    if not collection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")
    collection_id = collection.collection_id

    # delete any documents in the collection
    deleted_count = 0
    if delete_documents is True:
        statement = delete(Document).where(Document.collection_id == collection_id)
        result = await session.exec(statement)
        deleted_count = result.rowcount
    else:
        # check if there are any related documents
        statement = select(exists().where(Document.collection_id == collection_id)).select_from(Document)
        result = await session.exec(statement)
        has_documents = result.first()
        if has_documents:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="There are still documents in this collection. "
                                       "Set delete_documents=True to delete them.")

    # delete the collection
    await session.delete(collection)
    await session.commit()
    return {
        "msg": "Collection deleted",
        "collection_id": collection_id,
        "documents_deleted": deleted_count
    }


@router.get("/collections/{collection_id}",
            response_model=Collection,
            status_code=status.HTTP_200_OK,
            name="get_collection",
            description="Get a collection by ID")
async def get_collection(collection_id: str,
                         session: AsyncSession = Depends(get_session)) -> Collection:
    collection = await crud.get_collection_by_id(session=session, collection_id=collection_id)
    if not collection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")
    return collection


@router.patch("/collections/{collection_id}",
              response_model=Collection,
              status_code=status.HTTP_200_OK,
              name="update_collection",
              description="Update a collection")
async def update_collection(collection_id: str,
                            collection: CollectionUpdate,
                            session: AsyncSession = Depends(get_session)) -> Collection:
    db_collection = await crud.get_collection_by_id(session=session, collection_id=collection_id)
    if not db_collection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")
    collection_data = collection.model_dump(exclude_unset=True)
    # if collection_name is being updated, check if a collection with that name already exists
    if "collection_name" in collection_data:
        existing_collection = await crud.get_collection_by_name(
            session=session, collection_name=collection_data["collection_name"]
        )
        if existing_collection:
            raise HTTPException(status_code=400, detail="Collection with that name already exists")
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
    # get the collection
    collection = await crud.get_collection_by_id(session=session, collection_id=collection_id)
    if not collection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")

    # delete any documents in the collection
    deleted_count = 0
    if delete_documents is True:
        statement = delete(Document).where(Document.collection_id == collection_id)
        result = await session.exec(statement)
        deleted_count = result.rowcount
    else:
        # check if there are any related documents
        statement = select(exists().where(Document.collection_id == collection_id)).select_from(Document)
        result = await session.exec(statement)
        has_documents = result.first()
        if has_documents:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="There are still documents in this collection. "
                                       "Set delete_documents=True to delete them.")

    # delete the collection
    await session.delete(collection)
    await session.commit()
    return {
        "msg": "Collection deleted",
        "collection_id": collection_id,
        "documents_deleted": deleted_count
    }


@router.get("/collections/{collection_id}/documents",
            response_model=list[Document],
            status_code=status.HTTP_200_OK,
            name="Get documents in collection",
            description="Get documents in a collection")
async def get_collection_documents(collection_id: str,
                                   limit: int = Query(100, gt=0, le=1000),
                                   offset: int = 0,
                                   session: AsyncSession = Depends(get_session)) -> list[Document]:
    # get the collection
    collection = await crud.get_collection_by_id(session=session, collection_id=collection_id)
    if not collection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")
    # get documents in the collection
    result = await session.exec(
        select(Document).where(Document.collection_id == collection_id).limit(limit).offset(offset)
    )
    documents = result.all()
    return documents


@router.post("/collections/{collection_id}/documents",
             status_code=status.HTTP_201_CREATED,
             name="Add documents to collection",
             description="Add documents to a collection")
async def add_collection_documents(collection_id: str,
                                   documents: list[DocumentCreate],
                                   session: AsyncSession = Depends(get_session)) -> list[dict]:
    # get the collection
    collection = await crud.get_collection_by_id(session=session, collection_id=collection_id)
    if not collection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")
    # add documents
    docs_added = []
    for doc in documents:
        # Check if a document_id is provided and if it already exists
        if doc.document_id:
            existing_doc = await session.get(Document, doc.document_id)
            if existing_doc:
                raise HTTPException(status_code=400,
                                    detail={
                                        "msg": f"A document with this ID already exists: {doc.document_id}.",
                                        "document_id": str(doc.document_id),
                                    })
        document = Document(**doc.model_dump(), collection_id=collection.collection_id)
        session.add(document)
        await session.commit()
        await session.refresh(document)
        tasks = await generate_tasks_for_document(document)
        docs_added.append(
            {"document": document, "tasks": tasks}
        )
    return docs_added


# TODO: refactor logic to combine with `lexy.api.endpoints.documents.upload_documents`
@router.post("/collections/{collection_id}/documents/upload",
             status_code=status.HTTP_201_CREATED,
             name="Upload documents to collection",
             description="Upload documents to a collection")
async def upload_collection_documents(collection_id: str,
                                      files: list[UploadFile],
                                      session: AsyncSession = Depends(get_session),
                                      storage_client: StorageClient = Depends(get_storage_client)) -> list[dict]:
    # get the collection
    collection = await crud.get_collection_by_id(session=session, collection_id=collection_id)
    if not collection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")
    # TODO: get storage client from collection config
    # storage_client = get_storage_client(service=collection.config.get('storage_service', None))
    if collection.config.get('store_files') and not storage_client:
        storage_service = collection.config.get('storage_service', None)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Storage client not configured (service: {storage_service})")
    storage_bucket = collection.config.get('storage_bucket', settings.DEFAULT_STORAGE_BUCKET)
    if collection.config.get('store_files') and not storage_bucket:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Storage bucket not configured for this collection")
    storage_prefix = collection.config.get('storage_prefix', None)

    docs_uploaded = []

    for file in files:

        file_dict = {
            "content_type": file.content_type,
            "filename": file.filename,
            "size": file.size
        }

        # TODO: replace file.filename with the unique document id - will require saving the document in the DB first
        #  but for now, we're using the filename as the document_id, which is equivalent to the following:
        #    document_key = f"collections/{collection_id}/documents/{file.filename}"
        # uncomment the following line when ready
        # document_key = await construct_key_for_document(
        #     document=document,
        #     path_prefix=storage_prefix,
        #     filename=file.filename
        # )
        document_key = await construct_key_for_document(
            collection_id=collection_id,
            document_id=file.filename,
            path_prefix=storage_prefix
        )

        # TODO: move this to a separate parsing function - don't read into memory if not parsing
        file_content = await file.read()
        file_in_memory = BytesIO(file_content)
        file_in_memory.seek(0)

        # "pre-processing" based on file type
        if file.content_type.startswith('image/'):
            # logic for image files
            file_dict["type"] = 'image'
            doc_content = f"<Image({file.filename})>"
        elif file.content_type.startswith('text/'):
            # logic for text files
            file_dict["type"] = 'text'
            doc_content = file_content.decode("utf-8")
        elif file.content_type.startswith('application/pdf'):
            # logic for pdf files
            file_dict["type"] = 'pdf'
            doc_content = f"<PDF({file.filename})>"
        elif file.content_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            # logic for docx files
            file_dict["type"] = 'docx'
            doc_content = f"<DOCX({file.filename})>"
        elif file.content_type.startswith('video/'):
            # logic for video files
            file_dict["type"] = 'video'
            doc_content = f"<Video({file.filename})>"
        else:
            # logic for all other files
            file_dict["type"] = 'file'
            doc_content = f"<File({file.filename})>"

        # check for an existing doc based on content
        docs = await crud.get_documents_by_collection_id_and_content(
            session=session, collection_id=collection_id, content=doc_content
        )
        if docs:
            file_dict['document'] = docs[0]
            docs_uploaded.append(file_dict)
            continue

        # "post-processing" based on file type
        if file.content_type.startswith('image/'):
            # all we're doing here is getting the width and height - if we're generating thumbnails, we'll use this
            #  instance as the input
            img = Image.open(file_in_memory)
            width, height = img.size
            file_dict["image"] = {"width": width, "height": height}

            # generate thumbnails
            if collection.config.get('generate_thumbnails') and collection.config.get('store_files'):
                # generate thumbnails and upload to storage
                thumbnails = {}
                for dims in settings.IMAGE_THUMBNAIL_SIZES:
                    thumbnail_key = await construct_key_for_thumbnail(
                        dims=dims,
                        collection_id=collection_id,
                        document_id=file.filename,
                        path_prefix=storage_prefix
                    )
                    img_copy = img.copy()
                    img_copy.thumbnail(dims, Image.Resampling.LANCZOS)
                    img_byte_arr = BytesIO()
                    img_copy.save(img_byte_arr, format=img.format or 'JPEG')
                    # Note: img_byte_arr.seek(0) is run in storage_client.upload_object by default `rewind=True`
                    storage_thumbnail_meta = storage_client.upload_object(img_byte_arr, storage_bucket, thumbnail_key)
                    thumbnails[f"{dims[0]}x{dims[1]}"] = storage_thumbnail_meta
                file_dict["image"]["thumbnails"] = thumbnails
        elif file.content_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            # # example processing for docx
            # import docx
            # doc = docx.Document(BytesIO(file.file.read()))
            # num_paragraphs = len(doc.paragraphs)
            # num_tables = len(doc.tables)
            pass

        # Upload the file to storage
        if collection.config.get('store_files'):
            storage_document_meta = storage_client.upload_object(file_in_memory, storage_bucket, document_key)
            file_dict.update(storage_document_meta)

        document = Document(content=doc_content, meta=file_dict, collection_id=collection_id)
        session.add(document)
        await session.commit()
        await session.refresh(document)

        # generate tasks
        tasks = await generate_tasks_for_document(document, storage_client=storage_client)
        file_dict["document"] = document
        file_dict["tasks"] = tasks

        docs_uploaded.append(file_dict)

    return docs_uploaded


# TODO: Implement bulk update
# @router.patch("/collections/{collection_id}/documents",
#               status_code=status.HTTP_200_OK,
#               name="Bulk update documents in collection",
#               description="Update all documents in a collection")
# async def update_collection_documents(collection_id: str,
#                                       document_update: DocumentUpdate,
#                                       # documents: list[DocumentUpdate],
#                                       session: AsyncSession = Depends(get_session)) -> dict:
#     pass


@router.delete("/collections/{collection_id}/documents",
               status_code=status.HTTP_200_OK,
               name="Bulk delete documents in collection",
               description="Delete all documents in a collection")
async def delete_collection_documents(collection_id: str,
                                      session: AsyncSession = Depends(get_session)) -> dict:
    # get the collection
    collection = await crud.get_collection_by_id(session=session, collection_id=collection_id)
    if not collection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")
    # delete the documents
    statement = delete(Document).where(Document.collection_id == collection_id)
    result = await session.exec(statement)
    deleted_count = result.rowcount
    await session.commit()
    return {
        "msg": "Documents deleted",
        "collection_id": collection_id,
        "documents_deleted": deleted_count
    }
