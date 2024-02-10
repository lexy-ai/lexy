from sqlalchemy.orm import sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession, AsyncEngine
from sqlmodel import create_engine, SQLModel

from lexy.core.config import settings


sync_engine = create_engine(
    url=settings.sync_database_url,
    echo=settings.DB_ECHO_LOG
)

async_engine = AsyncEngine(create_engine(
    url=settings.async_database_url,
    echo=settings.DB_ECHO_LOG,
    future=True
))

async_session = sessionmaker(
    bind=async_engine, class_=AsyncSession, expire_on_commit=False
)


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session


async def create_db_and_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def recreate_db_and_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)
