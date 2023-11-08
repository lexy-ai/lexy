from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from lexy.db.session import get_session
from lexy.models.binding import (
    TransformerIndexBinding,
    TransformerIndexBindingCreate,
    TransformerIndexBindingUpdate,
    TransformerIndexBindingRead
)
from lexy.core.events import process_new_binding


router = APIRouter()


@router.get("/bindings",
            response_model=list[TransformerIndexBindingRead],
            status_code=status.HTTP_200_OK,
            name="get_bindings",
            description="Get all bindings")
async def get_bindings(session: AsyncSession = Depends(get_session)) -> list[TransformerIndexBindingRead]:
    result = await session.execute(select(TransformerIndexBinding))
    bindings = result.scalars().all()
    return bindings


@router.post("/bindings",
             status_code=status.HTTP_201_CREATED,
             name="add_binding",
             description="Create a new binding")
async def add_binding(binding: TransformerIndexBindingCreate, session: AsyncSession = Depends(get_session)) -> dict:
    binding = TransformerIndexBinding(**binding.dict())
    session.add(binding)
    await session.commit()
    await session.refresh(binding)
    processed_binding, tasks = await process_new_binding(binding)
    # now commit the binding again and refresh it - status should be updated
    session.add(processed_binding)
    await session.commit()
    await session.refresh(processed_binding)
    response = {"binding": processed_binding, "tasks": tasks}
    return response


@router.get("/bindings/{binding_id}",
            response_model=TransformerIndexBindingRead,
            status_code=status.HTTP_200_OK,
            name="get_binding",
            description="Get a binding")
async def get_binding(binding_id: int, session: AsyncSession = Depends(get_session)) -> TransformerIndexBindingRead:
    result = await session.execute(select(TransformerIndexBinding).where(TransformerIndexBinding.binding_id ==
                                                                         binding_id))
    binding = result.scalars().first()
    if not binding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Binding not found")
    return binding


@router.patch("/bindings/{binding_id}",
              status_code=status.HTTP_200_OK,
              name="update_binding",
              description="Update a binding")
async def update_binding(binding_id: int, binding: TransformerIndexBindingUpdate,
                         session: AsyncSession = Depends(get_session)) -> dict:
    result = await session.execute(select(TransformerIndexBinding).where(TransformerIndexBinding.binding_id ==
                                                                         binding_id))
    db_binding = result.scalars().first()
    if not db_binding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Binding not found")
    # record status in case it's changed
    old_status = db_binding.status

    update_data = binding.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_binding, key, value)
    session.add(db_binding)
    await session.commit()
    await session.refresh(db_binding)

    # if status has changed, process the binding
    if db_binding.status == "on" and old_status != "on":
        # TODO: this portion needs to be updated to reflect time stamps of tasks
        #  or to simply become part of an init script
        print(f"Binding status changed from '{old_status}' to 'on' - processing binding")
        processed_binding, tasks = await process_new_binding(db_binding)
        # now commit the binding again and refresh it - status should be updated
        session.add(processed_binding)
        await session.commit()
        await session.refresh(processed_binding)
        response = {"binding": processed_binding, "tasks": tasks}
        return response
    else:
        return db_binding


@router.delete("/bindings/{binding_id}",
               status_code=status.HTTP_200_OK,
               name="delete_binding",
               description="Delete a binding")
async def delete_binding(binding_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(TransformerIndexBinding).where(TransformerIndexBinding.binding_id ==
                                                                         binding_id))
    binding = result.scalars().first()
    if not binding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Binding not found")
    await session.delete(binding)
    await session.commit()
    return {"Say": "Binding deleted!"}
