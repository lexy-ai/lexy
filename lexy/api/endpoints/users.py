from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from lexy.api.deps import get_current_active_user, get_current_active_superuser, get_db
from lexy.models.user import User, UserCreate, UserRead, UserUpdate


router = APIRouter()


@router.get("/users",
            response_model=list[UserRead],
            status_code=status.HTTP_200_OK,
            name="get_users",
            description="Get all users (superuser only)",
            dependencies=[Depends(get_current_active_superuser)])
async def get_users(session: AsyncSession = Depends(get_db)) -> list[UserRead]:
    result = await session.execute(select(User))
    users = result.scalars().all()
    return users


@router.get("/users/me",
            response_model=UserRead,
            status_code=status.HTTP_200_OK,
            name="get_user_me",
            description="Get current user")
async def get_user_me(current_user: User = Depends(get_current_active_user)) -> UserRead:
    # TODO: change the next line to `return current_user` after updating SQLModel
    return UserRead.from_orm(current_user)


@router.post("/users",
             response_model=UserRead,
             status_code=status.HTTP_201_CREATED,
             name="create_user",
             description="Create a new user (superuser only)",
             dependencies=[Depends(get_current_active_superuser)])
async def create_user(user: UserCreate, session: AsyncSession = Depends(get_db)) -> UserRead:
    # check if user already exists
    result = await session.execute(select(User).where(User.email == user.email))
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User email is already registered")
    # create new user
    new_user = User.create(**user.dict())
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    return new_user


@router.get("/users/{user_id}",
            response_model=UserRead,
            status_code=status.HTTP_200_OK,
            name="get_user",
            description="Get a specific user (superuser only)",
            dependencies=[Depends(get_current_active_superuser)])
async def get_user(user_id: int, session: AsyncSession = Depends(get_db)) -> UserRead:
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    # TODO: change the next line to `return user` after updating SQLModel
    return UserRead.from_orm(user)


@router.delete("/users/{user_id}",
               status_code=status.HTTP_200_OK,
               name="delete_user",
               description="Delete a specific user (superuser only)",
               dependencies=[Depends(get_current_active_superuser)])
async def delete_user(user_id: int, session: AsyncSession = Depends(get_db)) -> dict[str, str]:
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    await session.delete(user)
    await session.commit()
    return {"detail": "User deleted", "user_id": user_id}


@router.patch("/users/{user_id}",
              response_model=UserRead,
              status_code=status.HTTP_200_OK,
              name="update_user",
              description="Update a specific user (superuser only)",
              dependencies=[Depends(get_current_active_superuser)])
async def update_user(user_id: int, user: UserUpdate, session: AsyncSession = Depends(get_db)) -> UserRead:
    db_user = await session.get(User, user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    update_data = user.dict(exclude_unset=True)
    for field in update_data:
        setattr(db_user, field, update_data[field])
    await session.commit()
    await session.refresh(db_user)
    # TODO: change the next line to `return db_user` after updating SQLModel
    return UserRead.from_orm(db_user)
