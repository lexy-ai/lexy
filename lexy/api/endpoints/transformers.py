from typing import List

from celery import group
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from lexy.core.celery_app import get_task_info
from lexy.core.celery_tasks import save_records_to_index
from lexy.db.session import get_session
from lexy.models.document import Document
from lexy.models.transformer import Transformer, TransformerCreate, TransformerUpdate
from lexy.transformers.counter import count_words
from lexy.transformers.embeddings import get_chunks, just_split, text_embeddings, text_embeddings_transformer


router = APIRouter()


@router.get("/transformers",
            response_model=list[Transformer],
            status_code=status.HTTP_200_OK,
            name="get_transformers",
            description="Get all transformers")
async def get_transformers(session: AsyncSession = Depends(get_session)) -> list[Transformer]:
    result = await session.execute(select(Transformer))
    transformers = result.scalars().all()
    return transformers


@router.post("/transformers",
             response_model=Transformer,
             status_code=status.HTTP_201_CREATED,
             name="add_transformer",
             description="Add a transformer")
async def add_transformer(transformer: TransformerCreate, session: AsyncSession = Depends(get_session)) -> Transformer:
    db_transformer = Transformer(**transformer.dict())
    session.add(db_transformer)
    await session.commit()
    await session.refresh(db_transformer)
    return db_transformer


@router.get("/transformers/{transformer_id}",
            response_model=Transformer,
            status_code=status.HTTP_200_OK,
            name="get_transformer",
            description="Get a transformer")
async def get_transformer(transformer_id: str, session: AsyncSession = Depends(get_session)) -> Transformer:
    result = await session.execute(select(Transformer).where(Transformer.transformer_id == transformer_id))
    transformer = result.scalars().first()
    if not transformer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transformer not found")
    return transformer


@router.patch("/transformers/{transformer_id}",
              response_model=Transformer,
              status_code=status.HTTP_200_OK,
              name="update_transformer",
              description="Update a transformer")
async def update_transformer(transformer_id: str, transformer: TransformerUpdate,
                             session: AsyncSession = Depends(get_session)) -> Transformer:
    result = await session.execute(select(Transformer).where(Transformer.transformer_id == transformer_id))
    db_transformer = result.scalars().first()
    if not db_transformer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transformer not found")
    transformer_data = transformer.dict(exclude_unset=True)
    for key, value in transformer_data.items():
        setattr(db_transformer, key, value)
    session.add(db_transformer)
    await session.commit()
    await session.refresh(db_transformer)
    return db_transformer


@router.delete("/transformers/{transformer_id}",
               status_code=status.HTTP_200_OK,
               name="delete_transformer",
               description="Delete a transformer")
async def delete_transformer(transformer_id: str, session: AsyncSession = Depends(get_session)) -> dict:
    result = await session.execute(select(Transformer).where(Transformer.transformer_id == transformer_id))
    transformer = result.scalars().first()
    if not transformer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transformer not found")
    await session.delete(transformer)
    await session.commit()
    return {"Say": "Transformer deleted!"}


@router.post("/embed/string",
             response_model=dict,
             status_code=status.HTTP_200_OK,
             name="embed_string",
             description="Get embeddings for query string")
async def embed_string(string: str) -> dict:
    task = text_embeddings.apply_async(args=[string])
    result = task.get()
    return {"embedding": result.tolist()}


@router.post("/embed/documents",
             response_model=dict,
             status_code=status.HTTP_202_ACCEPTED,
             name="embed_documents",
             description="Create embeddings for a list of documents")
async def embed_documents(documents: List[Document], index_id: str = "default_text_embeddings") -> dict:
    tasks = []
    for doc in documents:
        task = text_embeddings_transformer.apply_async(
            args=[doc.content],
            link=save_records_to_index.s(document_id=doc.document_id, text=doc.content, index_id=index_id)
        )
        tasks.append({"task_id": task.id, "document_id": doc.document_id})
    return {"tasks": tasks}


@router.post("/count",
             response_model=dict,
             status_code=status.HTTP_200_OK,
             name="get_word_count",
             description="Get word count for a document")
async def get_word_count(document: Document) -> dict:
    task = count_words.apply_async(args=[document.content])
    return {"tasks": [{"task_id": task.id, "document_id": document.document_id}]}


@router.post("/split",
             response_model=dict,
             status_code=status.HTTP_200_OK,
             name="get_split",
             description="Get split for a document")
async def get_split(document: Document) -> dict:
    task = just_split.apply_async(args=[document.content])
    return {"tasks": [{"task_id": task.id, "document_id": document.document_id}]}


@router.post("/chunks",
             response_model=dict,
             status_code=status.HTTP_200_OK,
             name="get_document_chunks",
             description="Get chunks for a document")
async def get_document_chunks(document: Document) -> dict:
    task = get_chunks.apply_async(
        args=[document.content],
        kwargs={"chunk_size": 2}
    )
    return {"tasks": [{"task_id": task.id, "document_id": document.document_id}]}


@router.get("/tasks/{task_id}",
            response_model=dict,
            status_code=status.HTTP_200_OK,
            name="get_task_status",
            description="Get task status")
async def get_task_status(task_id: str) -> dict:
    return get_task_info(task_id)


@router.post("/parallel",
             response_model=dict,
             status_code=status.HTTP_200_OK,
             name="get_embeddings_parallel",
             description="Get embeddings for multiple documents in parallel")
async def get_embeddings_parallel(documents: List[Document]) -> dict:
    tasks = []
    for doc in documents:
        tasks.append(text_embeddings.s([doc.content]))
    job = group(tasks)
    result = job.apply_async()
    ret_values = result.get()
    return dict(zip([str(d.document_id) for d in documents], [r.tolist() for r in ret_values]))
