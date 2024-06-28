from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlmodel import create_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from lexy.core.config import settings


sync_engine: Engine = create_engine(
    url=settings.sync_database_url, echo=settings.DB_ECHO_LOG, future=True
)

async_engine: AsyncEngine = create_async_engine(
    url=settings.async_database_url, echo=settings.DB_ECHO_LOG, future=True
)

async_session = async_sessionmaker(
    bind=async_engine, class_=AsyncSession, expire_on_commit=False
)


def get_sync_engine() -> Engine:
    return sync_engine


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
