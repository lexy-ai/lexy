import pytest
import asyncio
import httpx

from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from sqlmodel import create_engine, SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession, AsyncEngine

from lexy.main import app
from lexy.models.collection import Collection

# base_url = "http://127.0.0.1:9900/"
base_url = "http://localhost:9900"

# engine = create_engine(
#     url="postgresql+asyncpg://postgres:postgres@localhost/lexy_tests",
#     echo=False,
#     future=True
# )
# TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
#
# @pytest.fixture(scope="session")
# def db():
#     yield TestSession()

# async_engine = AsyncEngine(create_engine(
#     url="postgresql+asyncpg://postgres:postgres@localhost:6543/lexy_tests",
#     echo=False,
#     future=True
# ))

# FIXME: rewrite this using guide here: https://sqlmodel.tiangolo.com/tutorial/fastapi/tests/


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def client():
    with TestClient(app=app, base_url=base_url) as c:
    # with httpx.Client(app=app, base_url=base_url, follow_redirects=True) as c:
        yield c


@pytest.fixture(scope="session")
async def async_client():
    async with httpx.AsyncClient(app=app, base_url=base_url, follow_redirects=True) as c:
        yield c


@pytest.fixture(scope="session")
def async_engine():
    return AsyncEngine(create_engine(
        url="postgresql+asyncpg://postgres:postgres@localhost:6543/lexy_tests",
        echo=True,
        future=True
    ))


# @pytest.fixture()
# def test_db():
#     SQLModel.metadata.create_all(bind=engine)
#     yield
#     SQLModel.metadata.drop_all(bind=engine)


@pytest.fixture(scope="session")
async def async_session(async_engine):
    async_session = sessionmaker(bind=async_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session


@pytest.fixture(scope='session', autouse=True)
async def reset_db(async_engine, async_session):
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)

    collection = Collection(collection_id="default", description="Default collection")
    async_session.add(collection)
    await async_session.commit()
    await async_session.refresh(collection)
