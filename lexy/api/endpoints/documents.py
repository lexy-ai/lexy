from io import BytesIO

import boto3
from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile
from PIL import Image
from sqlmodel import delete, select
from sqlmodel.ext.asyncio.session import AsyncSession

from lexy.db.session import get_session
from lexy.storage.client import get_s3_client, generate_presigned_urls_for_document
from lexy.models.collection import Collection
from lexy.models.document import Document, DocumentCreate, DocumentUpdate
from lexy.core.config import settings
from lexy.core.events import generate_tasks_for_document


router = APIRouter()


# TODO: move this somewhere else
def create_thumbnails_s3(image, sizes, s3_client, s3_bucket, s3_base_path, document_id) -> dict:
    """ Create thumbnails for a given PIL Image object and upload to S3.

    Args:
        image (Image.Image): The source image.
        sizes (list of tuples): A list of size tuples (width, height) for the thumbnails.
        s3_client (boto3.client): The S3 client.
        s3_bucket (str): The name of the S3 bucket.
        s3_base_path (str): The base path inside the S3 bucket.
        document_id (str): The identifier for the document object.

    Returns:
        Dict: Each entry contains a thumbnail size and its corresponding S3 path.
    """
    thumbnails = {}

    for size in sizes:
        img_copy = image.copy()
        img_copy.thumbnail(size, Image.Resampling.LANCZOS)

        img_byte_arr = BytesIO()
        img_format = image.format or 'JPEG'
        img_copy.save(img_byte_arr, format=img_format)
        img_byte_arr.seek(0)

        s3_key = f"{s3_base_path}/{size[0]}x{size[1]}/{document_id}"
        s3_client.upload_fileobj(img_byte_arr, s3_bucket, s3_key)
        thumbnails[f"{size[0]}x{size[1]}"] = {
            "s3_bucket": s3_bucket,
            "s3_key": s3_key,
            "s3_uri": f"s3://{s3_bucket}/{s3_key}",
            "s3_url": f"https://{settings.s3_bucket}.s3.amazonaws.com/{s3_key}",
        }
    return thumbnails


@router.get("/documents",
            response_model=list[Document],
            status_code=status.HTTP_200_OK,
            name="get_documents",
            description="Get all documents in a collection")
async def get_documents(collection_id: str | None = "default",
                        limit: int = Query(100, gt=0, le=1000),
                        offset: int = 0,
                        session: AsyncSession = Depends(get_session)) -> list[Document]:
    result = await session.execute(select(Document)
                                   .where(Document.collection_id == collection_id)
                                   .limit(limit)
                                   .offset(offset))
    documents = result.scalars().all()
    return documents


@router.post("/documents",
             status_code=status.HTTP_201_CREATED,
             name="add_documents",
             description="Add documents to a collection")
async def add_documents(documents: list[DocumentCreate],
                        collection_id: str | None = "default",
                        session: AsyncSession = Depends(get_session)) -> list[dict]:
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
        document = Document(**doc.dict(), collection_id=collection_id)
        session.add(document)
        await session.commit()
        await session.refresh(document)
        tasks = await generate_tasks_for_document(document)
        docs_added.append(
            {"document": document, "tasks": tasks}
        )
    return docs_added


@router.post("/documents/upload",
             status_code=status.HTTP_201_CREATED,
             name="upload_documents",
             description="Upload documents to a collection")
async def upload_documents(files: list[UploadFile],
                           collection_id: str = "default",
                           session: AsyncSession = Depends(get_session),
                           s3_client: boto3.client = Depends(get_s3_client)) -> list[dict]:
    upload_files = []

    collection = await session.execute(select(Collection).where(Collection.collection_id == collection_id))
    collection = collection.scalars().first()
    if not collection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")

    for file in files:

        file_dict = {
            "content_type": file.content_type,
            "filename": file.filename,
            "headers": file.headers,
            "size": file.size,
        }

        file_content = await file.read()
        file_in_memory = BytesIO(file_content)
        file_in_memory.seek(0)

        print(file_dict)
        file_dict.pop("headers")

        if file.content_type.startswith('image/'):
            # logic for image files
            file_dict["type"] = 'image'

            # check for duplicates first
            result = await session.execute(select(Document)
                                           .where(Document.content == f"<Image({file.filename})>")
                                           .where(Document.collection_id == collection_id))
            document = result.scalars().first()
            if document:
                file_dict['document'] = document
                upload_files.append(file_dict)
                continue

            # all we're doing here is getting the width and height - if we're generating thumbnails, we'll use this
            #  instance as the input
            img = Image.open(file_in_memory)
            width, height = img.size
            file_dict["image"] = {"width": width, "height": height}

            # Upload the file to S3
            if collection.config.get('store_files'):
                # TODO: replace file.filename with the unique document id
                s3_key = f"collections/{collection_id}/documents/{file.filename}"
                file.file.seek(0)
                s3_client.upload_fileobj(file.file, settings.s3_bucket, s3_key)

                file_dict["s3_bucket"] = settings.s3_bucket
                file_dict["s3_key"] = s3_key
                file_dict["s3_url"] = f"https://{settings.s3_bucket}.s3.amazonaws.com/{s3_key}"
                file_dict["s3_uri"] = f"s3://{settings.s3_bucket}/{s3_key}"

            # generate thumbnails
            if collection.config.get('generate_thumbnails') and collection.config.get('store_files'):
                thumbnails = create_thumbnails_s3(image=img,
                                                  sizes=settings.image_thumbnail_sizes,
                                                  s3_client=s3_client,
                                                  s3_bucket=settings.s3_bucket,
                                                  s3_base_path=f"collections/{collection_id}/thumbnails",
                                                  document_id=file.filename)
                file_dict["image"]["thumbnails"] = thumbnails

            document = Document(content=f"<Image({file.filename})>", meta=file_dict, collection_id=collection_id)
            session.add(document)
            await session.commit()
            await session.refresh(document)

            # generate tasks
            tasks = await generate_tasks_for_document(document, s3_client=s3_client)
            file_dict["document"] = document
            file_dict["tasks"] = tasks

        elif file.content_type.startswith('text/'):
            # logic for text files
            file_dict["type"] = 'text'
            document = Document(content=file_content.decode("utf-8"), meta=file_dict, collection_id=collection_id)
            # session.add(document)
            # await session.commit()
            # await session.refresh(document)
            file_dict['document'] = document

        elif file.content_type.startswith('application/pdf'):
            # logic for pdf files
            file_dict["type"] = 'pdf'
            document = Document(content=f"<PDF({file.filename})>", meta=file_dict, collection_id=collection_id)
            # session.add(document)
            # await session.commit()
            # await session.refresh(document)
            file_dict['document'] = document

        elif file.content_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            # logic for docx files
            file_dict["type"] = 'docx'
            # # example processing for docx
            # import docx
            # docx = docx.Document(io.BytesIO(file.file.read()))
            # num_paragraphs = len(doc.paragraphs)
            document = Document(content=f"<DOCX({file.filename})>", meta=file_dict, collection_id=collection_id)
            # session.add(document)
            # await session.commit()
            # await session.refresh(document)
            file_dict['document'] = document

        upload_files.append(file_dict)

    return upload_files


@router.delete("/documents",
               status_code=status.HTTP_200_OK,
               name="bulk_delete_documents",
               description="Bulk delete all documents in a collection")
async def bulk_delete_documents(collection_id: str, session: AsyncSession = Depends(get_session)) -> dict:
    statement = delete(Document).where(Document.collection_id == collection_id)
    result = await session.execute(statement)
    deleted_count = result.rowcount
    await session.commit()
    return {"Say": "Documents deleted!", "deleted_count": deleted_count}


@router.get("/documents/{document_id}",
            response_model=Document,
            status_code=status.HTTP_200_OK,
            name="get_document",
            description="Get a document")
async def get_document(document_id: str, session: AsyncSession = Depends(get_session)) -> Document:
    result = await session.execute(select(Document).where(Document.document_id == document_id))
    document = result.scalars().first()
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return document


@router.get("/documents/{document_id}/urls",
            status_code=status.HTTP_200_OK,
            name="get_document_urls",
            description="Get presigned URLs for a document")
async def get_document_urls(document_id: str,
                            expiration: int = Query(3600, gt=0, le=3600),
                            session: AsyncSession = Depends(get_session),
                            s3_client: boto3.client = Depends(get_s3_client)) -> dict:
    result = await session.execute(select(Document).where(Document.document_id == document_id))
    document = result.scalars().first()
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return generate_presigned_urls_for_document(document, s3_client, expiration)


@router.patch("/documents/{document_id}",
              status_code=status.HTTP_200_OK,
              name="update_document",
              description="Update a document")
async def update_document(document_id: str,
                          document: DocumentUpdate,
                          session: AsyncSession = Depends(get_session),
                          s3_client: boto3.client = Depends(get_s3_client)) -> dict:
    result = await session.execute(select(Document).where(Document.document_id == document_id))
    db_document = result.scalars().first()
    if not db_document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    document_data = document.dict(exclude_unset=True)
    for key, value in document_data.items():
        setattr(db_document, key, value)
    session.add(db_document)
    await session.commit()
    await session.refresh(db_document)
    tasks = await generate_tasks_for_document(db_document, s3_client=s3_client)
    return {"document": db_document, "tasks": tasks}


@router.delete("/documents/{document_id}",
               status_code=status.HTTP_200_OK,
               name="delete_document",
               description="Delete a document")
async def delete_document(document_id: str, session: AsyncSession = Depends(get_session)) -> dict:
    result = await session.execute(select(Document).where(Document.document_id == document_id))
    document = result.scalars().first()
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    await session.delete(document)
    await session.commit()
    return {"Say": "Document deleted!"}
