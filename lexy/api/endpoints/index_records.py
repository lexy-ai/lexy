from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import asc, func, select
from sqlalchemy.orm import aliased
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from lexy.db.session import get_session
from lexy.models.document import Document
from lexy.models.index import Index
from lexy.transformers.embeddings import text_embeddings


router = APIRouter()

document_tbl = aliased(Document, name="document_tbl")


@router.get("/indexes/{index_id}/records",
            response_model=list[dict],
            status_code=status.HTTP_200_OK,
            name="get_records",
            description="Get records for an index")
async def get_records(index_id: str = "default_text_embeddings", document_id: str | None = None,
                      session: AsyncSession = Depends(get_session)) -> list[dict]:
    result = await session.execute(select(Index).where(Index.index_id == index_id))
    index = result.scalars().first()
    if not index:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Index {index_id} not found")
    index_tbl = SQLModel.metadata.tables.get(index.index_table_name)
    if document_id:
        result = await session.execute(select(index_tbl).where(index_tbl.c.document_id == document_id))
    else:
        result = await session.execute(select(index_tbl))
    index_records = result.all()
    return index_records  # type: ignore


@router.get("/indexes/{index_id}/records/query",
            response_model=dict,
            status_code=status.HTTP_200_OK,
            name="query_records",
            description="Query all records for an index")
async def query_records(query_string: str, k: int = 5, query_field: str = "embedding",
                        index_id: str = "default_text_embeddings", session: AsyncSession = Depends(get_session)) \
        -> dict:

    # get embedding for query string
    task = text_embeddings.apply_async(args=[query_string], priority=10)
    result = task.get()
    query_embedding = result.tolist()

    # get index table
    result = await session.execute(select(Index).where(Index.index_id == index_id))
    index = result.scalars().first()
    if not index:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Index '{index_id}' not found")
    index_tbl = SQLModel.metadata.tables.get(index.index_table_name)

    # get query column and index fields to return
    query_column = index_tbl.c.get(query_field, None)
    if query_column is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Field '{query_field}' not found in index '{index_id}'")
    return_index_fields = [index_tbl.c[k] for k, v in index.index_fields.items() if v["type"] != "embedding"]

    # query index table
    search_result = await session.execute(
        select(index_tbl.c.document_id,
               index_tbl.c.custom_id,
               index_tbl.c.meta,
               index_tbl.c.index_record_id,
               document_tbl.content.label("document_content"),
               func.abs(query_column.op("<->")(query_embedding)).label("abs_distance"),
               # not adding a function here causes the query to fail for some reason
               func.pow(query_column.op("<->")(query_embedding), 1).label("distance"),
               *return_index_fields
               )
        .join(document_tbl, index_tbl.c.document_id == document_tbl.document_id)
        .order_by(asc("distance"))
        .limit(k))
    search_results = search_result.all()
    return {"search_results": search_results}


@router.get("/indexes/{index_id}/records/{index_record_id}",
            status_code=status.HTTP_200_OK,
            name="get_record",
            description="Get a record from an index")
async def get_record(index_record_id: str, index_id: str, session: AsyncSession = Depends(get_session)) -> dict:
    index_result = await session.execute(select(Index).where(Index.index_id == index_id))
    index = index_result.scalars().first()
    if not index:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Index '{index_id}' not found")
    index_tbl = SQLModel.metadata.tables.get(index.index_table_name)
    result = await session.execute(select(index_tbl).where(index_tbl.c.index_record_id == index_record_id))
    index_record = result.first()
    if not index_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Index record '{index_record_id}' not found in index '{index_id}'")
    return index_record
