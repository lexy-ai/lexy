import logging
from typing import Optional, TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from lexy import crud
from lexy.db.session import get_session
from lexy.storage.client import get_storage_client
from lexy.models.binding import Binding, BindingCreate, BindingRead, BindingUpdate
from lexy.core.events import process_new_binding

if TYPE_CHECKING:
    from lexy.storage.client import StorageClient


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
router = APIRouter()


@router.get("/bindings",
            response_model=list[BindingRead],
            status_code=status.HTTP_200_OK,
            name="get_bindings",
            description="Get all bindings")
async def get_bindings(session: AsyncSession = Depends(get_session)) -> list[BindingRead]:
    result = await session.exec(select(Binding))
    bindings = result.all()
    return bindings


# TODO: change to the following after SQLAlchemy 2.0: https://stackoverflow.com/a/75947988
@router.post("/bindings",
             response_model=dict[str, BindingRead | list[dict]],
             status_code=status.HTTP_201_CREATED,
             name="add_binding",
             description="Create a new binding")
async def add_binding(binding: BindingCreate,
                      session: AsyncSession = Depends(get_session),
                      storage_client: Optional["StorageClient"] = Depends(get_storage_client)) \
        -> dict[str, BindingRead | list[dict]]:
    # set collection_id based on collection_id or collection_name
    if binding.collection_id:
        collection = await crud.get_collection_by_id(session=session, collection_id=binding.collection_id)
    else:
        # BindingCreate model validator ensures that one of the two is provided (id or name)
        collection = await crud.get_collection_by_name(session=session, collection_name=binding.collection_name)
    if not collection:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Collection not found")
    binding.collection_id = collection.collection_id

    transformer = await crud.get_transformer_by_id(session=session, transformer_id=binding.transformer_id)
    if not transformer:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Transformer not found")
    index = await crud.get_index_by_id(session=session, index_id=binding.index_id)
    if not index:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Index not found")

    # TODO: switch to pattern `db_binding = Binding.model_validate(binding)` once issue is resolved.
    #  Currently SQLModel is not serializing the nested model, leading to the error 'Filter is not JSON
    #  Serializable'. But using `Binding(**binding.model_dump())` leaves binding.filter as a dict type.
    #  See issue: https://github.com/tiangolo/sqlmodel/issues/63
    db_binding = Binding(**binding.model_dump())
    session.add(db_binding)
    await session.commit()
    await session.refresh(db_binding)

    # process the binding and generate document tasks
    processed_binding, tasks = await session.run_sync(
        process_new_binding, db_binding, storage_client=storage_client
    )
    # now commit the binding again and refresh it - status should be updated
    session.add(processed_binding)
    await session.commit()
    await session.refresh(processed_binding)

    response = {"binding": processed_binding, "tasks": tasks}
    return response


@router.get("/bindings/{binding_id}",
            response_model=BindingRead,
            status_code=status.HTTP_200_OK,
            name="get_binding",
            description="Get a binding")
async def get_binding(binding_id: int,
                      session: AsyncSession = Depends(get_session)) -> BindingRead:
    result = await session.exec(select(Binding).where(Binding.binding_id == binding_id))
    binding = result.first()
    if not binding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Binding not found")
    return binding


# TODO: change to the following after SQLAlchemy 2.0: https://stackoverflow.com/a/75947988
@router.patch("/bindings/{binding_id}",
              status_code=status.HTTP_200_OK,
              name="update_binding",
              description="Update a binding")
async def update_binding(binding_id: int,
                         binding: BindingUpdate,
                         session: AsyncSession = Depends(get_session),
                         storage_client: Optional["StorageClient"] = Depends(get_storage_client)) \
        -> dict[str, BindingRead | list[dict]]:
    result = await session.exec(select(Binding).where(Binding.binding_id == binding_id))
    db_binding = result.first()
    if not db_binding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Binding not found")
    # record status in case it's changed
    old_status = db_binding.status

    update_data = binding.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_binding, key, value)
    if db_binding.filter:
        db_binding.filter = jsonable_encoder(db_binding.filter)
    session.add(db_binding)
    await session.commit()
    await session.refresh(db_binding)

    # if status has changed, process the binding
    if db_binding.status == "on" and old_status != "on":
        # TODO: this portion needs to be updated to reflect time stamps of tasks
        #  or to simply become part of an init script
        print(f"Binding status changed from '{old_status}' to 'on' - processing binding")
        processed_binding, tasks = await session.run_sync(
            process_new_binding, db_binding, storage_client=storage_client
        )
        # now commit the binding again and refresh it - status should be updated
        session.add(processed_binding)
        await session.commit()
        await session.refresh(processed_binding)
        response = {"binding": processed_binding, "tasks": tasks}
    else:
        response = {"binding": db_binding, "tasks": []}
    return response


@router.delete("/bindings/{binding_id}",
               status_code=status.HTTP_200_OK,
               name="delete_binding",
               description="Delete a binding")
async def delete_binding(binding_id: int,
                         session: AsyncSession = Depends(get_session)) -> dict:
    result = await session.exec(select(Binding).where(Binding.binding_id == binding_id))
    binding = result.first()
    if not binding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Binding not found")
    await session.delete(binding)
    await session.commit()
    return {"msg": "Binding deleted", "binding_id": binding_id}
