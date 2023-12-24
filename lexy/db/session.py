import boto3
from sqlalchemy.orm import sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession, AsyncEngine
from sqlmodel import create_engine, SQLModel

from lexy.core.config import settings


sync_engine = create_engine(
    url=settings.sync_database_url,
    echo=settings.db_echo_log
)

async_engine = AsyncEngine(create_engine(
    url=settings.async_database_url,
    echo=settings.db_echo_log,
    future=True
))

async_session = sessionmaker(
    bind=async_engine, class_=AsyncSession, expire_on_commit=False
)


async def get_s3_client() -> boto3.client:
    client_kwargs = {}
    if settings.aws_access_key_id and settings.aws_secret_access_key:
        client_kwargs["aws_access_key_id"] = settings.aws_access_key_id
        client_kwargs["aws_secret_access_key"] = settings.aws_secret_access_key
    if settings.aws_region:
        client_kwargs["region_name"] = settings.aws_region
    return boto3.client('s3', **client_kwargs)


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
