from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile
from PIL import Image
from sqlmodel import delete, select
from sqlmodel.ext.asyncio.session import AsyncSession

from lexy import crud
from lexy.db.session import get_session
from lexy.storage.client import (
    construct_key_for_document,
    construct_key_for_thumbnail,
    generate_signed_urls_for_document,
    get_storage_client,
    StorageClient,
)
from lexy.models.document import Document, DocumentCreate, DocumentUpdate
from lexy.core.config import settings
from lexy.core.events import generate_tasks_for_document


router = APIRouter()


@router.get(
    "/documents",
    response_model=list[Document],
    status_code=status.HTTP_200_OK,
    name="get_documents",
    description="Get documents in a collection",
)
async def get_documents(
    collection_name: str = "default",
    limit: int = Query(100, gt=0, le=1000),
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
) -> list[Document]:
    # get the collection
    collection = await crud.get_collection_by_name(
        session=session, collection_name=collection_name
    )
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found"
        )

    # get documents
    result = await session.exec(
        select(Document)
        .where(Document.collection_id == collection.collection_id)
        .limit(limit)
        .offset(offset)
    )
    documents = result.all()
    return documents


@router.post(
    "/documents",
    status_code=status.HTTP_201_CREATED,
    name="add_documents",
    description="Add documents to a collection",
)
async def add_documents(
    documents: list[DocumentCreate],
    collection_name: str = "default",
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    # get the collection
    collection = await crud.get_collection_by_name(
        session=session, collection_name=collection_name
    )
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found"
        )

    docs_added = []
    for doc in documents:
        # Check if a document_id is provided and if it already exists
        if doc.document_id:
            existing_doc = await session.get(Document, doc.document_id)
            if existing_doc:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "msg": f"A document with this ID already exists: {doc.document_id}.",
                        "document_id": str(doc.document_id),
                    },
                )
        document = Document(**doc.model_dump(), collection_id=collection.collection_id)
        session.add(document)
        await session.commit()
        await session.refresh(document)
        tasks = await generate_tasks_for_document(document)
        docs_added.append({"document": document, "tasks": tasks})
    return docs_added


# TODO: refactor logic to combine with `lexy.api.endpoints.collections.upload_collection_documents`
@router.post(
    "/documents/upload",
    status_code=status.HTTP_201_CREATED,
    name="upload_documents",
    description="Upload documents to a collection",
)
async def upload_documents(
    files: list[UploadFile],
    collection_name: str = "default",
    session: AsyncSession = Depends(get_session),
    storage_client: StorageClient = Depends(get_storage_client),
) -> list[dict]:
    # get the collection
    collection = await crud.get_collection_by_name(
        session=session, collection_name=collection_name
    )
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found"
        )
    collection_id = collection.collection_id
    # TODO: get storage client from collection config
    # storage_client = get_storage_client(service=collection.config.get('storage_service', None))
    if collection.config.get("store_files") and not storage_client:
        storage_service = collection.config.get("storage_service", None)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Storage client not configured (service: {storage_service})",
        )
    storage_bucket = collection.config.get(
        "storage_bucket", settings.DEFAULT_STORAGE_BUCKET
    )
    if collection.config.get("store_files") and not storage_bucket:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Storage bucket not configured for this collection",
        )
    storage_prefix = collection.config.get("storage_prefix", None)

    docs_uploaded = []

    for file in files:
        file_dict = {
            "content_type": file.content_type,
            "filename": file.filename,
            "size": file.size,
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
            path_prefix=storage_prefix,
        )

        # TODO: move this to a separate parsing function - don't read into memory if not parsing
        file_content = await file.read()
        file_in_memory = BytesIO(file_content)
        file_in_memory.seek(0)

        # "pre-processing" based on file type
        if file.content_type.startswith("image/"):
            # logic for image files
            file_dict["type"] = "image"
            doc_content = f"<Image({file.filename})>"
        elif file.content_type.startswith("text/"):
            # logic for text files
            file_dict["type"] = "text"
            doc_content = file_content.decode("utf-8")
        elif file.content_type.startswith("application/pdf"):
            # logic for pdf files
            file_dict["type"] = "pdf"
            doc_content = f"<PDF({file.filename})>"
        elif (
            file.content_type
            == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ):
            # logic for docx files
            file_dict["type"] = "docx"
            doc_content = f"<DOCX({file.filename})>"
        elif file.content_type.startswith("video/"):
            # logic for video files
            file_dict["type"] = "video"
            doc_content = f"<Video({file.filename})>"
        else:
            # logic for all other files
            file_dict["type"] = "file"
            doc_content = f"<File({file.filename})>"

        # check for an existing doc based on content
        docs = await crud.get_documents_by_collection_id_and_content(
            session=session, collection_id=collection_id, content=doc_content
        )
        if docs:
            file_dict["document"] = docs[0]
            docs_uploaded.append(file_dict)
            continue

        # "post-processing" based on file type
        if file.content_type.startswith("image/"):
            # all we're doing here is getting the width and height - if we're generating thumbnails, we'll use this
            #  instance as the input
            img = Image.open(file_in_memory)
            width, height = img.size
            file_dict["image"] = {"width": width, "height": height}

            # generate thumbnails
            if collection.config.get("generate_thumbnails") and collection.config.get(
                "store_files"
            ):
                # generate thumbnails and upload to storage
                thumbnails = {}
                for dims in settings.IMAGE_THUMBNAIL_SIZES:
                    thumbnail_key = await construct_key_for_thumbnail(
                        dims=dims,
                        collection_id=collection_id,
                        document_id=file.filename,
                        path_prefix=storage_prefix,
                    )
                    img_copy = img.copy()
                    img_copy.thumbnail(dims, Image.Resampling.LANCZOS)
                    img_byte_arr = BytesIO()
                    img_copy.save(img_byte_arr, format=img.format or "JPEG")
                    # Note: img_byte_arr.seek(0) is run in storage_client.upload_object by default `rewind=True`
                    storage_thumbnail_meta = storage_client.upload_object(
                        img_byte_arr, storage_bucket, thumbnail_key
                    )
                    thumbnails[f"{dims[0]}x{dims[1]}"] = storage_thumbnail_meta
                file_dict["image"]["thumbnails"] = thumbnails
        elif (
            file.content_type
            == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ):
            # # example processing for docx
            # import docx
            # doc = docx.Document(BytesIO(file.file.read()))
            # num_paragraphs = len(doc.paragraphs)
            # num_tables = len(doc.tables)
            pass

        # Upload the file to storage
        if collection.config.get("store_files"):
            storage_document_meta = storage_client.upload_object(
                file_in_memory, storage_bucket, document_key
            )
            file_dict.update(storage_document_meta)

        document = Document(
            content=doc_content, meta=file_dict, collection_id=collection_id
        )
        session.add(document)
        await session.commit()
        await session.refresh(document)

        # generate tasks
        tasks = await generate_tasks_for_document(
            document, storage_client=storage_client
        )
        file_dict["document"] = document
        file_dict["tasks"] = tasks

        docs_uploaded.append(file_dict)

    return docs_uploaded


@router.delete(
    "/documents",
    status_code=status.HTTP_200_OK,
    name="bulk_delete_documents",
    description="Bulk delete all documents in a collection",
)
async def bulk_delete_documents(
    collection_name: str, session: AsyncSession = Depends(get_session)
) -> dict:
    # get the collection
    collection = await crud.get_collection_by_name(
        session=session, collection_name=collection_name
    )
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found"
        )
    # delete documents
    statement = delete(Document).where(
        Document.collection_id == collection.collection_id
    )
    result = await session.exec(statement)
    deleted_count = result.rowcount
    await session.commit()
    return {
        "msg": "Documents deleted",
        "collection_id": collection.collection_id,
        "deleted_count": deleted_count,
    }


@router.get(
    "/documents/{document_id}",
    response_model=Document,
    status_code=status.HTTP_200_OK,
    name="get_document",
    description="Get a document",
)
async def get_document(
    document_id: str, session: AsyncSession = Depends(get_session)
) -> Document:
    result = await session.exec(
        select(Document).where(Document.document_id == document_id)
    )
    document = result.first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )
    return document


@router.get(
    "/documents/{document_id}/urls",
    status_code=status.HTTP_200_OK,
    name="get_document_urls",
    description="Get presigned URLs for a document",
)
async def get_document_urls(
    document_id: str,
    expiration: int = Query(3600, gt=0, le=3600),
    session: AsyncSession = Depends(get_session),
    storage_client: StorageClient = Depends(get_storage_client),
) -> dict:
    result = await session.exec(
        select(Document).where(Document.document_id == document_id)
    )
    document = result.first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )
    # TODO: get storage client from document config
    if document.is_stored_object and not storage_client:
        storage_service = document.meta.get("storage_service")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Storage client not configured (service: {storage_service})",
        )
    return generate_signed_urls_for_document(document, storage_client, expiration)


@router.patch(
    "/documents/{document_id}",
    status_code=status.HTTP_200_OK,
    name="update_document",
    description="Update a document",
)
async def update_document(
    document_id: str,
    document: DocumentUpdate,
    session: AsyncSession = Depends(get_session),
    storage_client: StorageClient = Depends(get_storage_client),
) -> dict:
    result = await session.exec(
        select(Document).where(Document.document_id == document_id)
    )
    db_document = result.first()
    if not db_document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )
    document_data = document.model_dump(exclude_unset=True)
    for key, value in document_data.items():
        setattr(db_document, key, value)
    session.add(db_document)
    await session.commit()
    await session.refresh(db_document)
    tasks = await generate_tasks_for_document(
        db_document, storage_client=storage_client
    )
    return {"document": db_document, "tasks": tasks}


@router.delete(
    "/documents/{document_id}",
    status_code=status.HTTP_200_OK,
    name="delete_document",
    description="Delete a document",
)
async def delete_document(
    document_id: str, session: AsyncSession = Depends(get_session)
) -> dict:
    result = await session.exec(
        select(Document).where(Document.document_id == document_id)
    )
    document = result.first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )
    await session.delete(document)
    await session.commit()
    return {"msg": "Document deleted", "document_id": document_id}
