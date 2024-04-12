from io import BytesIO

import boto3
from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile
from PIL import Image
from sqlmodel import delete, select
from sqlmodel.ext.asyncio.session import AsyncSession

from lexy import crud
from lexy.db.session import get_session
from lexy.storage.client import get_s3_client, generate_presigned_urls_for_document
from lexy.models.document import Document, DocumentCreate, DocumentUpdate
from lexy.core.config import settings
from lexy.core.events import generate_tasks_for_document


router = APIRouter()


def upload_file_to_s3(file: UploadFile, s3_client: boto3.client, s3_bucket: str, s3_key: str) -> dict:
    """ Upload a file to S3.

    Args:
        file (UploadFile): The file to upload.
        s3_client (boto3.client): The S3 client.
        s3_bucket (str): The name of the S3 bucket.
        s3_key (str): The S3 key for the file.

    Returns:
        Dict: The S3 path and URL for the file.
    """
    file.file.seek(0)
    s3_client.upload_fileobj(file.file, s3_bucket, s3_key)
    return {
        "s3_bucket": s3_bucket,
        "s3_key": s3_key,
        "s3_url": f"https://{s3_bucket}.s3.amazonaws.com/{s3_key}",
        "s3_uri": f"s3://{s3_bucket}/{s3_key}",
    }


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
            "s3_url": f"https://{s3_bucket}.s3.amazonaws.com/{s3_key}",
        }
    return thumbnails


@router.get("/documents",
            response_model=list[Document],
            status_code=status.HTTP_200_OK,
            name="get_documents",
            description="Get documents in a collection")
async def get_documents(collection_name: str = "default",
                        limit: int = Query(100, gt=0, le=1000),
                        offset: int = 0,
                        session: AsyncSession = Depends(get_session)) -> list[Document]:
    # get the collection
    collection = await crud.get_collection_by_name(session=session, collection_name=collection_name)
    if not collection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")

    # get documents
    result = await session.exec(
        select(Document).where(Document.collection_id == collection.collection_id).limit(limit).offset(offset)
    )
    documents = result.all()
    return documents


@router.post("/documents",
             status_code=status.HTTP_201_CREATED,
             name="add_documents",
             description="Add documents to a collection")
async def add_documents(documents: list[DocumentCreate],
                        collection_name: str = "default",
                        session: AsyncSession = Depends(get_session)) -> list[dict]:
    # get the collection
    collection = await crud.get_collection_by_name(session=session, collection_name=collection_name)
    if not collection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")

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


@router.post("/documents/upload",
             status_code=status.HTTP_201_CREATED,
             name="upload_documents",
             description="Upload documents to a collection")
async def upload_documents(files: list[UploadFile],
                           collection_name: str = "default",
                           session: AsyncSession = Depends(get_session),
                           s3_client: boto3.client = Depends(get_s3_client)) -> list[dict]:
    # get the collection
    collection = await crud.get_collection_by_name(session=session, collection_name=collection_name)
    if not collection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")
    collection_id = collection.collection_id

    upload_files = []

    for file in files:

        file_dict = {
            "content_type": file.content_type,
            "filename": file.filename,
            "headers": file.headers,
            "size": file.size,
        }

        # TODO: replace file.filename with the unique document id
        s3_bucket = settings.S3_BUCKET
        s3_key = f"collections/{collection_id}/documents/{file.filename}"

        file_content = await file.read()
        file_in_memory = BytesIO(file_content)
        file_in_memory.seek(0)

        print(file_dict)
        file_dict.pop("headers")

        if file.content_type.startswith('image/'):
            # logic for image files
            file_dict["type"] = 'image'
            doc_content = f"<Image({file.filename})>"

            # check for duplicates
            docs = await crud.get_documents_by_collection_id_and_content(
                session=session, collection_id=collection_id, content=doc_content
            )
            if docs:
                file_dict['document'] = docs[0]
                upload_files.append(file_dict)
                continue
            # result = await session.exec(
            #     select(Document)
            #     .where(Document.content == f"<Image({file.filename})>")
            #     .where(Document.collection_id == collection_id)
            # )
            # document = result.first()
            # if document:
            #     file_dict['document'] = document
            #     upload_files.append(file_dict)
            #     continue

            # all we're doing here is getting the width and height - if we're generating thumbnails, we'll use this
            #  instance as the input
            img = Image.open(file_in_memory)
            width, height = img.size
            file_dict["image"] = {"width": width, "height": height}

            # # Upload the file to S3
            # if collection.config.get('store_files'):
            #     # TODO: replace file.filename with the unique document id
            #     s3_bucket = settings.S3_BUCKET
            #     s3_key = f"collections/{collection_id}/documents/{file.filename}"
            #     file.file.seek(0)
            #     s3_client.upload_fileobj(file.file, settings.S3_BUCKET, s3_key)
            #
            #     file_dict["s3_bucket"] = settings.S3_BUCKET
            #     file_dict["s3_key"] = s3_key
            #     file_dict["s3_url"] = f"https://{settings.S3_BUCKET}.s3.amazonaws.com/{s3_key}"
            #     file_dict["s3_uri"] = f"s3://{settings.S3_BUCKET}/{s3_key}"

            # generate thumbnails
            if collection.config.get('generate_thumbnails') and collection.config.get('store_files'):
                thumbnails = create_thumbnails_s3(image=img,
                                                  sizes=settings.IMAGE_THUMBNAIL_SIZES,
                                                  s3_client=s3_client,
                                                  s3_bucket=settings.S3_BUCKET,
                                                  s3_base_path=f"collections/{collection_id}/thumbnails",
                                                  document_id=file.filename)
                file_dict["image"]["thumbnails"] = thumbnails

            # Upload the file to S3
            if collection.config.get('store_files'):
                s3_meta = upload_file_to_s3(file, s3_client, s3_bucket, s3_key)
                file_dict.update(s3_meta)

            document = Document(content=doc_content, meta=file_dict, collection_id=collection_id)
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
            doc_content = file_content.decode("utf-8")

            # check for duplicates
            docs = await crud.get_documents_by_collection_id_and_content(
                session=session, collection_id=collection_id, content=doc_content
            )
            if docs:
                file_dict['document'] = docs[0]
                upload_files.append(file_dict)
                continue

            # Upload the file to S3
            if collection.config.get('store_files'):
                s3_meta = upload_file_to_s3(file, s3_client, s3_bucket, s3_key)
                file_dict.update(s3_meta)

            document = Document(content=doc_content, meta=file_dict, collection_id=collection_id)
            session.add(document)
            await session.commit()
            await session.refresh(document)

            # generate tasks
            tasks = await generate_tasks_for_document(document, s3_client=s3_client)
            file_dict['document'] = document
            file_dict['tasks'] = tasks

        elif file.content_type.startswith('application/pdf'):
            # logic for pdf files
            file_dict["type"] = 'pdf'
            doc_content = f"<PDF({file.filename})>"

            # check for duplicates
            docs = await crud.get_documents_by_collection_id_and_content(
                session=session, collection_id=collection_id, content=doc_content
            )
            if docs:
                file_dict['document'] = docs[0]
                upload_files.append(file_dict)
                continue
            # result = await session.exec(
            #     select(Document)
            #     .where(Document.content == f"<PDF({file.filename})>")
            #     .where(Document.collection_id == collection_id)
            # )
            # document = result.first()
            # if document:
            #     file_dict['document'] = document
            #     upload_files.append(file_dict)
            #     continue

            # Upload the file to S3
            if collection.config.get('store_files'):
                s3_meta = upload_file_to_s3(file, s3_client, s3_bucket, s3_key)
                file_dict.update(s3_meta)

            document = Document(content=doc_content, meta=file_dict, collection_id=collection_id)
            session.add(document)
            await session.commit()
            await session.refresh(document)
            file_dict['document'] = document

            # generate tasks
            tasks = await generate_tasks_for_document(document, s3_client=s3_client)
            file_dict["document"] = document
            file_dict["tasks"] = tasks

        elif file.content_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            # logic for docx files
            file_dict["type"] = 'docx'
            doc_content = f"<DOCX({file.filename})>"
            # # example processing for docx
            # import docx
            # docx = docx.Document(io.BytesIO(file.file.read()))
            # num_paragraphs = len(doc.paragraphs)

            # check for duplicates
            docs = await crud.get_documents_by_collection_id_and_content(
                session=session, collection_id=collection_id, content=doc_content
            )
            if docs:
                file_dict['document'] = docs[0]
                upload_files.append(file_dict)
                continue

            # Upload the file to S3
            if collection.config.get('store_files'):
                s3_meta = upload_file_to_s3(file, s3_client, s3_bucket, s3_key)
                file_dict.update(s3_meta)

            document = Document(content=doc_content, meta=file_dict, collection_id=collection_id)
            session.add(document)
            await session.commit()
            await session.refresh(document)

            # generate tasks
            tasks = await generate_tasks_for_document(document, s3_client=s3_client)
            file_dict['document'] = document
            file_dict['tasks'] = tasks

        elif file.content_type.startswith('video/'):
            # logic for video files
            file_dict["type"] = 'video'
            doc_content = f"<Video({file.filename})>"

            # check for duplicates
            docs = await crud.get_documents_by_collection_id_and_content(
                session=session, collection_id=collection_id, content=doc_content
            )
            if docs:
                file_dict['document'] = docs[0]
                upload_files.append(file_dict)
                continue

            # Upload the file to S3
            if collection.config.get('store_files'):
                s3_meta = upload_file_to_s3(file, s3_client, s3_bucket, s3_key)
                file_dict.update(s3_meta)

            document = Document(content=doc_content, meta=file_dict, collection_id=collection_id)
            session.add(document)
            await session.commit()
            await session.refresh(document)

            # generate tasks
            tasks = await generate_tasks_for_document(document, s3_client=s3_client)
            file_dict['document'] = document
            file_dict['tasks'] = tasks

        else:
            # logic for other files
            file_dict["type"] = 'file'
            doc_content = f"<File({file.filename})>"

            # check for duplicates
            docs = await crud.get_documents_by_collection_id_and_content(
                session=session, collection_id=collection_id, content=doc_content
            )
            if docs:
                file_dict['document'] = docs[0]
                upload_files.append(file_dict)
                continue

            # Upload the file to S3
            if collection.config.get('store_files'):
                s3_meta = upload_file_to_s3(file, s3_client, s3_bucket, s3_key)
                file_dict.update(s3_meta)

            document = Document(content=doc_content, meta=file_dict, collection_id=collection_id)
            session.add(document)
            await session.commit()
            await session.refresh(document)

            # generate tasks
            tasks = await generate_tasks_for_document(document, s3_client=s3_client)
            file_dict['document'] = document
            file_dict['tasks'] = tasks

        if 'document' in file_dict:
            upload_files.append(file_dict)

    return upload_files


@router.delete("/documents",
               status_code=status.HTTP_200_OK,
               name="bulk_delete_documents",
               description="Bulk delete all documents in a collection")
async def bulk_delete_documents(collection_name: str,
                                session: AsyncSession = Depends(get_session)) -> dict:
    # get the collection
    collection = await crud.get_collection_by_name(session=session, collection_name=collection_name)
    if not collection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")
    # delete documents
    statement = delete(Document).where(Document.collection_id == collection.collection_id)
    result = await session.exec(statement)
    deleted_count = result.rowcount
    await session.commit()
    return {
        "msg": "Documents deleted",
        "collection_id": collection.collection_id,
        "deleted_count": deleted_count
    }


@router.get("/documents/{document_id}",
            response_model=Document,
            status_code=status.HTTP_200_OK,
            name="get_document",
            description="Get a document")
async def get_document(document_id: str,
                       session: AsyncSession = Depends(get_session)) -> Document:
    result = await session.exec(select(Document).where(Document.document_id == document_id))
    document = result.first()
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
    result = await session.exec(select(Document).where(Document.document_id == document_id))
    document = result.first()
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
    result = await session.exec(select(Document).where(Document.document_id == document_id))
    db_document = result.first()
    if not db_document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    document_data = document.model_dump(exclude_unset=True)
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
async def delete_document(document_id: str,
                          session: AsyncSession = Depends(get_session)) -> dict:
    result = await session.exec(select(Document).where(Document.document_id == document_id))
    document = result.first()
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    await session.delete(document)
    await session.commit()
    return {"msg": "Document deleted", "document_id": document_id}
