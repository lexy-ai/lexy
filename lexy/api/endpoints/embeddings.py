from fastapi import APIRouter, Depends, status
from sqlalchemy import func
from sqlalchemy.orm import aliased
from sqlalchemy.sql.expression import select, asc
from sqlmodel.ext.asyncio.session import AsyncSession

from lexy.db.session import get_session
from lexy.models.document import Document
from lexy.models.embedding import Embedding, EmbeddingCreate
from lexy.transformers.embeddings import custom_transformer, get_default_transformer


router = APIRouter()

embedding_tbl = aliased(Embedding, name="embedding_tbl")
document_tbl = aliased(Document, name="document_tbl")


@router.get("/embeddings",
            response_model=list[Embedding],
            status_code=status.HTTP_200_OK,
            name="get_embeddings",
            description="Get all embeddings")
async def get_embeddings(session: AsyncSession = Depends(get_session)) -> list[Embedding]:
    result = await session.execute(select(Embedding))
    embeddings = result.scalars().all()
    return embeddings


@router.post("/embeddings",
             status_code=status.HTTP_201_CREATED,
             name="add_embeddings",
             description="Add embeddings")
async def add_embeddings(embeddings: list[EmbeddingCreate], session: AsyncSession = Depends(get_session)) -> dict:
    for emb in embeddings:
        session.add(Embedding(**emb.dict()))
    await session.commit()
    return {"Say": "Embeddings added!"}


@router.post("/embeddings/query",
             response_model=dict,
             status_code=status.HTTP_200_OK,
             name="query_embeddings",
             description="Query for similar documents")
async def query_embeddings(query_string: str, k: int = 5, session: AsyncSession = Depends(get_session)) -> dict:
    doc = Document(content=query_string)
    task = custom_transformer.apply_async(args=[doc, get_default_transformer()], priority=10)
    result = task.get()
    query_embedding = result.tolist()
    search_result = await session.execute(
        select(embedding_tbl.document_id,
               embedding_tbl.embedding_id,
               embedding_tbl.text,
               document_tbl.content.label("document_content"),
               func.abs(embedding_tbl.embedding.op("<->")(query_embedding)).label("abs_distance"),
               # not adding a function here causes the query to fail for some reason
               func.pow(embedding_tbl.embedding.op("<->")(query_embedding), 1).label("distance")
               )
        .join(document_tbl, embedding_tbl.document_id == document_tbl.document_id)
        .order_by(asc("distance"))
        .limit(k))
    search_results = search_result.all()
    return {"search_results": search_results}
