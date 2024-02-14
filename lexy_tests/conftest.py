import asyncio
import httpx
import pytest

from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, SQLModel, create_engine, delete
from sqlmodel.ext.asyncio.session import AsyncSession, AsyncEngine

from lexy.core.config import TestAppSettings
from lexy.db.init_db import add_default_data_to_db, add_first_superuser_to_db
from lexy.db.session import get_session
from lexy.api.deps import get_db
from lexy.main import app as lexy_test_app
from lexy import models


test_settings = TestAppSettings()
DB_WARNING_MSG = "There's a good chance you're about to drop the wrong database! Double check your test settings."
assert test_settings.POSTGRES_DB != "lexy", DB_WARNING_MSG
test_settings.DB_ECHO_LOG = False

# TODO: need to update IndexManager and Celery to use the test database


@pytest.fixture(scope="session")
def settings() -> TestAppSettings:
    """Fixture for test settings."""
    print("settings: ", test_settings)
    return test_settings


@pytest.fixture(scope="session")
def sync_engine(settings: TestAppSettings):
    """Create a SQLAlchemy sync engine for the test database."""
    engine = create_engine(
        url=settings.sync_database_url,
        echo=settings.DB_ECHO_LOG
    )
    print(f"sync_engine.url: {engine.url}")
    return engine


@pytest.fixture(scope="session")
def async_engine(settings: TestAppSettings):
    """Create a SQLAlchemy async engine for the test database."""
    engine = AsyncEngine(
        create_engine(
            url=settings.async_database_url,
            echo=settings.DB_ECHO_LOG
        )
    )
    print(f"async_engine.url: {engine.url}")
    return engine


@pytest.fixture(scope="session")
def create_test_database(sync_engine):
    """Create test database and tables."""
    with sync_engine.begin() as conn:
        # If using SQLModel, replace YourBaseModel with SQLModel.metadata
        print(f"Creating test DB tables with engine.url: {sync_engine.url}")
        SQLModel.metadata.create_all(conn)
        print("-- Kk, I created the tables --\n" * 3)
    yield
    with sync_engine.begin() as conn:
        print(f"Dropping test DB tables with engine.url: {sync_engine.url}")
        # TODO: need to make sure this isn't using the wrong instance of SQLModel.metadata
        # SQLModel.metadata.drop_all(conn)


# TODO: need to figure out how to make this function scoped
@pytest.fixture(scope="session")
def sync_session(sync_engine, create_test_database):
    # """Create a new sync session for each test case."""
    session = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)
    with session() as s:
        yield s


@pytest.fixture(scope="session")
def seed_data(sync_session: Session, settings: TestAppSettings):
    """Seed the test database with data."""
    # Add seed data to the test database
    print("Seeding the test database with data")
    # Add first superuser
    add_first_superuser_to_db(session=sync_session, settings=settings)
    # Add default data
    add_default_data_to_db(session=sync_session)
    # Uncomment the next line if you want to add sample documents
    # add_sample_docs_to_db(session=sync_session)
    yield
    # Clean up the seed data after the tests
    print("deleting seed data")
    models_to_delete = [
        models.User,
        models.Binding,
        models.Index,
        models.Document,
        models.Collection,
        models.Transformer
    ]
    for model in models_to_delete:
        # another way to do it
        # sync_session.query(model).delete()
        result = sync_session.execute(delete(model))
        deleted_count = result.rowcount
        print(f"deleting {deleted_count} {model.__name__} objects")
    sync_session.commit()


# TODO: need to figure out how to make this function scoped
@pytest.fixture(scope="session")
async def async_session(async_engine, create_test_database, seed_data):
    # """Create a new async session for each test case."""
    async_session = sessionmaker(
        bind=async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session


@pytest.fixture(scope="session")
def client(sync_session: Session, seed_data) -> TestClient:
    """Fixture for providing a synchronous TestClient configured for testing."""
    # Override get_session and get_db dependencies to use the test database session
    lexy_test_app.dependency_overrides[get_session] = lambda: async_session
    lexy_test_app.dependency_overrides[get_db] = lambda: async_session
    with TestClient(app=lexy_test_app) as c:
        yield c
    lexy_test_app.dependency_overrides.clear()  # Reset overrides after tests


@pytest.fixture(scope="session")
async def async_client(async_session: AsyncSession) -> httpx.AsyncClient:
    """Fixture for providing an asynchronous TestClient configured for testing."""
    # Override get_session and get_db dependencies to use the test database session
    lexy_test_app.dependency_overrides[get_session] = lambda: async_session
    lexy_test_app.dependency_overrides[get_db] = lambda: async_session
    async with httpx.AsyncClient(app=lexy_test_app, base_url="http://test") as ac:
        yield ac
    lexy_test_app.dependency_overrides.clear()  # Reset overrides after tests


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()
