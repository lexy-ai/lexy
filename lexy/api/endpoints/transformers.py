from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from lexy.core.celery_tasks import celery, convert_arrays_to_lists
from lexy.db.session import get_session
from lexy.models.document import DocumentCreate
from lexy.models.transformer import Transformer, TransformerCreate, TransformerUpdate


router = APIRouter()


@router.get("/transformers",
            response_model=list[Transformer],
            status_code=status.HTTP_200_OK,
            name="get_transformers",
            description="Get all transformers")
async def get_transformers(session: AsyncSession = Depends(get_session)) -> list[Transformer]:
    result = await session.exec(select(Transformer))
    transformers = result.all()
    return transformers


@router.post("/transformers",
             response_model=Transformer,
             status_code=status.HTTP_201_CREATED,
             name="add_transformer",
             description="Add a transformer")
async def add_transformer(transformer: TransformerCreate,
                          session: AsyncSession = Depends(get_session)) -> Transformer:
    # check if transformer already exists
    existing_transformer = await session.get(Transformer, transformer.transformer_id)
    if existing_transformer:
        raise HTTPException(status_code=400, detail="Transformer with that ID already exists")

    db_transformer = Transformer.model_validate(transformer)
    session.add(db_transformer)
    await session.commit()
    await session.refresh(db_transformer)
    return db_transformer


@router.get("/transformers/{transformer_id}",
            response_model=Transformer,
            status_code=status.HTTP_200_OK,
            name="get_transformer",
            description="Get a transformer")
async def get_transformer(transformer_id: str,
                          session: AsyncSession = Depends(get_session)) -> Transformer:
    result = await session.exec(select(Transformer).where(Transformer.transformer_id == transformer_id))
    transformer = result.first()
    if not transformer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transformer not found")
    return transformer


@router.patch("/transformers/{transformer_id}",
              response_model=Transformer,
              status_code=status.HTTP_200_OK,
              name="update_transformer",
              description="Update a transformer")
async def update_transformer(transformer_id: str,
                             transformer: TransformerUpdate,
                             session: AsyncSession = Depends(get_session)) -> Transformer:
    result = await session.exec(select(Transformer).where(Transformer.transformer_id == transformer_id))
    db_transformer = result.first()
    if not db_transformer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transformer not found")
    transformer_data = transformer.model_dump(exclude_unset=True)
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
async def delete_transformer(transformer_id: str,
                             session: AsyncSession = Depends(get_session)) -> dict:
    result = await session.exec(select(Transformer).where(Transformer.transformer_id == transformer_id))
    transformer = result.first()
    if not transformer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transformer not found")
    await session.delete(transformer)
    await session.commit()
    return {"msg": "Transformer deleted", "transformer_id": transformer_id}


@router.post("/transformers/{transformer_id}",
             response_model=dict,
             status_code=status.HTTP_200_OK,
             name="transform_document",
             description="Transform a document")
async def transform_document(transformer_id: str,
                             document: DocumentCreate,
                             transformer_params: dict = None,
                             content_only: bool = False,
                             session: AsyncSession = Depends(get_session)) -> dict:
    result = await session.exec(select(Transformer).where(Transformer.transformer_id == transformer_id))
    transformer = result.first()
    if not transformer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transformer not found")

    task_name = transformer.celery_task_name
    if content_only:
        task_arg = document.content
    else:
        task_arg = document

    task = celery.send_task(
        task_name,
        args=[task_arg],
        kwargs=transformer_params,
    )
    result = task.get()
    response = {"task_id": task.id, "result": result}
    return convert_arrays_to_lists(response)
