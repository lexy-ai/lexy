import io

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, status, UploadFile
from PIL import Image
from sqlalchemy import asc, func, select
from sqlalchemy.orm import aliased
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from lexy.core.events import celery
from lexy.db.session import get_session
from lexy.models.document import Document
from lexy.models.index import Index
from lexy.models.transformer import Transformer


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


@router.post("/indexes/{index_id}/records/query",
             response_model=dict,
             status_code=status.HTTP_200_OK,
             name="query_records",
             description="Query all records for an index")
async def query_records(query_text: str = Form(None),
                        query_image: UploadFile = File(None),
                        k: int = 5,
                        query_field: str = "embedding",
                        index_id: str = "default_text_embeddings",
                        return_fields: list[str] = Query(None),
                        return_document: bool = False,
                        embedding_model: str = None,
                        session: AsyncSession = Depends(get_session)) -> dict:
    if query_text and query_image:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Please submit either 'query_text' or 'query_image', not both.")
    elif query_text:
        query = query_text
    elif query_image:
        file_content = await query_image.read()
        query = Image.open(io.BytesIO(file_content))
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Please submit either 'query_text' or 'query_image'.")

    # get index table and query column
    result = await session.execute(select(Index).where(Index.index_id == index_id))
    index = result.scalars().first()
    if not index:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Index '{index_id}' not found")
    index_tbl = SQLModel.metadata.tables.get(index.index_table_name)
    query_column = index_tbl.c.get(query_field, None)
    if query_column is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Field '{query_field}' not found in index '{index_id}'")

    # get embedding model using index_fields
    if embedding_model is None:
        try:
            embedding_model: str = index.index_fields[query_field]["extras"]["model"]
        except KeyError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"Index field '{query_field}' does not have an embedding model. You can "
                                       f"specify one using the 'embedding_model' parameter.")
    # if multimodal, assign model based on query type
    if '*' in embedding_model:
        if isinstance(query, Image.Image):
            embedding_model = embedding_model.replace("*", "image")
        else:
            embedding_model = embedding_model.replace("*", "text")

    # get embedding for query string
    transformer = await session.execute(select(Transformer).where(Transformer.transformer_id == embedding_model))
    transformer = transformer.scalars().first()
    if not transformer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Transformer '{embedding_model}' not found")
    task = celery.send_task(transformer.celery_task_name, args=[query], priority=10)
    result = task.get()
    if isinstance(result, list):
        query_embedding = result
    else:
        query_embedding = result.tolist()

    # get index fields to return
    if return_fields:
        return_index_fields = []
        # get any related document fields
        for rf in return_fields:
            if rf.startswith("document."):
                attribute_name = rf.split(".")[1]
                return_index_fields.append(getattr(document_tbl, attribute_name).label(rf))
            else:
                return_index_fields.append(index_tbl.c[rf])
    else:
        return_index_fields = [index_tbl.c[k] for k, v in index.index_fields.items() if v["type"] != "embedding"]

    # if there's nothing else to return, return document content
    # TODO: remove this condition once we have auto-embed option which will return the embedded content
    if return_document is False and len(return_index_fields) == 0:
        return_index_fields.append(document_tbl.content.label("document.content"))

    base_query = (
        select(index_tbl.c.document_id,
               index_tbl.c.custom_id,
               index_tbl.c.meta,
               index_tbl.c.index_record_id,
               func.abs(query_column.op("<->")(query_embedding)).label("abs_distance"),
               # not adding a function here causes the query to fail for some reason
               func.pow(query_column.op("<->")(query_embedding), 1).label("distance"),
               *return_index_fields
               ).join(document_tbl, index_tbl.c.document_id == document_tbl.document_id)
    )

    # optionally return the document object
    # using this as a hack to grab document fields - will refactor to use SQLModel objects instead of tables
    doc_prefix = "doc_"
    if return_document:
        document_columns = [getattr(document_tbl, field).label(doc_prefix + field)
                            for field in document_tbl.__table__.columns.keys()]
        base_query = base_query.add_columns(*document_columns)

    # query index table
    search_result = await session.execute(
        base_query.order_by(asc("distance")).limit(k)
    )
    search_results = search_result.all()

    # process results to nest document fields under "document" key - will get rid of this once we use SQLModel objects
    formatted_results = []
    for row in search_results:
        result_dict = row._asdict()  # Convert result row to dictionary
        document_data = {}
        if return_document:
            # Extract prefixed Document fields and nest them under 'document' key
            for field in document_tbl.__table__.columns.keys():
                prefixed_name = doc_prefix + field
                document_data[field] = result_dict.pop(prefixed_name)
            result_dict["document"] = document_data
        formatted_results.append(result_dict)

    return {"search_results": formatted_results}


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
