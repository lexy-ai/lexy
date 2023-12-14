from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import delete, select
from sqlmodel.ext.asyncio.session import AsyncSession

from lexy.db.session import get_session
from lexy.models.document import Document, DocumentCreate, DocumentUpdate
from lexy.core.events import generate_tasks_for_document


router = APIRouter()


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
async def add_documents(documents: list[DocumentCreate], collection_id: str | None = "default",
                        session: AsyncSession = Depends(get_session)) -> list[dict]:
    docs_added = []
    for doc in documents:
        document = Document(**doc.dict(), collection_id=collection_id)
        session.add(document)
        await session.commit()
        await session.refresh(document)
        tasks = await generate_tasks_for_document(document)
        docs_added.append(
            {"document": document, "tasks": tasks}
        )
    return docs_added


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


@router.patch("/documents/{document_id}",
              status_code=status.HTTP_200_OK,
              name="update_document",
              description="Update a document")
async def update_document(document_id: str, document: DocumentUpdate,
                          session: AsyncSession = Depends(get_session)) -> dict:
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
    tasks = await generate_tasks_for_document(db_document)
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
