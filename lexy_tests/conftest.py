import os

import asyncio
import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import close_all_sessions
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel, create_engine, delete
from sqlmodel.ext.asyncio.session import AsyncSession
from asgi_lifespan import LifespanManager

from lexy.core.config import settings, TestAppSettings
from lexy.core.celery_config import settings as celery_settings
from lexy.db.init_db import add_default_data_to_db, add_first_superuser_to_db
from lexy.db.session import get_session
from lexy import models

os.environ["CELERY_BROKER_URL"] = celery_settings.broker_url
os.environ["CELERY_RESULT_BACKEND"] = celery_settings.result_backend

# We need to import the app **after** forcefully setting the env vars, since Celery doesn't
#  let you assign any value other than the environment variable if one is set.
#  See https://github.com/celery/celery/issues/4284.
from lexy.main import app as lexy_test_app  # noqa: F401


# the value of LEXY_CONFIG and CELERY_CONFIG are set using pytest-env plugin in pyproject.toml
assert os.environ.get("LEXY_CONFIG") == "testing", "LEXY_CONFIG is not set to 'testing'"
assert os.environ.get("CELERY_CONFIG") == "testing", "CELERY_CONFIG is not set to 'testing'"


test_settings = settings
test_celery_settings = celery_settings


DB_WARNING_MSG = ("There's a good chance you're about to drop the wrong database! "
                  "Double check your test settings.")
assert test_settings.POSTGRES_DB != "lexy", DB_WARNING_MSG


CELERY_DB_WARNING_MSG = ("Test instance of Celery is configured to store results in the wrong database! "
                         "Double check your test settings.")
backend_url_obj = make_url(test_celery_settings.result_backend)
assert backend_url_obj.database != "lexy", CELERY_DB_WARNING_MSG


@pytest.fixture(scope="session")
def settings() -> TestAppSettings:
    """Fixture for test settings."""
    print(f"{test_settings = }")
    return test_settings


@pytest.fixture(scope="session")
def sync_engine(settings: TestAppSettings):
    """Create a SQLAlchemy sync engine for the test database."""
    engine = create_engine(
        url=settings.sync_database_url,
        echo=settings.DB_ECHO_LOG,
        future=True
    )
    print(f"sync_engine.url: {engine.url}")
    assert engine.url.database != "lexy", DB_WARNING_MSG
    return engine


@pytest.fixture(scope="session")
def async_engine(settings: TestAppSettings):
    """Create a SQLAlchemy async engine for the test database."""
    engine = create_async_engine(
        settings.async_database_url,
        echo=settings.DB_ECHO_LOG,
        future=True,
        poolclass=NullPool
    )
    print(f"async_engine.url: {engine.url}")
    assert engine.url.database != "lexy", DB_WARNING_MSG
    return engine


@pytest.fixture(scope="session")
def create_test_database(sync_engine, celery_session_app):
    """Create test database and tables."""
    with sync_engine.begin() as conn:
        print(f"Creating test DB tables with engine.url: {sync_engine.url}")
        SQLModel.metadata.create_all(conn)
        print("Created test DB tables")
    yield
    with sync_engine.begin() as conn:
        lexy_table_names = ", ".join(SQLModel.metadata.tables.keys())
        celery_table_names = ", ".join(celery_session_app.backend.task_cls.metadata.tables.keys())
        celery_tables = celery_session_app.backend.task_cls.metadata.sorted_tables
        print(f"Dropping test DB tables..."
              f"\n\tengine.url: {sync_engine.url}"
              f"\n\tlexy_table_names: {lexy_table_names}"
              f"\n\tcelery_table_names: {celery_table_names}")
        SQLModel.metadata.drop_all(conn)
        celery_session_app.backend.task_cls.metadata.drop_all(conn, tables=celery_tables)
        print("Dropped test DB tables")


@pytest.fixture(scope="session")
def seed_data(settings: TestAppSettings, sync_engine: Engine, create_test_database):
    """Seed the test database with data."""
    # Create a local sync session for seeding the test database
    local_sessionmaker = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)
    local_session = local_sessionmaker()
    # Add seed data to the test database
    print("Seeding the test database with data")
    # Add first superuser
    add_first_superuser_to_db(session=local_session, settings=settings)
    # Add default data
    add_default_data_to_db(session=local_session)
    # Uncomment the next line if you want to add sample documents
    # add_sample_docs_to_db(session=local_session)
    yield
    # Clean up the seed data after the tests
    print("Deleting test DB data...")
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
        # local_session.query(model).delete()
        result = local_session.execute(delete(model))
        deleted_count = result.rowcount
        print(f"\tdeleting {deleted_count} {model.__name__} objects")
    local_session.commit()
    close_all_sessions()
    print("Deleted test DB data")


@pytest.fixture(scope="session")
async def test_app(seed_data) -> FastAPI:
    async with LifespanManager(lexy_test_app):
        yield lexy_test_app


@pytest.fixture(scope="function")
def sync_session(sync_engine, test_app):
    """Create a new sync session for each test case."""
    session = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)
    with session() as s:
        yield s


@pytest.fixture(scope="function")
async def async_session(async_engine, test_app):
    """Create a new async session for each test case."""
    async_session = async_sessionmaker(
        bind=async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session


@pytest.fixture(scope="function")
def client(test_app, async_session: AsyncSession) -> TestClient:
    """Fixture for providing a synchronous TestClient configured for testing."""
    async def override_get_session():
        async with async_session as session:
            yield session

    # Override get_session dependency to use the test database session
    test_app.dependency_overrides[get_session] = override_get_session

    client = TestClient(app=test_app, raise_server_exceptions=False)
    yield client

    del test_app.dependency_overrides[get_session]  # Reset overrides after tests


@pytest.fixture(scope="function")
async def async_client(test_app, async_session: AsyncSession) -> httpx.AsyncClient:
    """Fixture for providing an asynchronous TestClient configured for testing."""
    async def override_get_session():
        async with async_session as session:
            yield session

    # Override get_session dependency to use the test database session
    test_app.dependency_overrides[get_session] = override_get_session

    async with httpx.AsyncClient(app=test_app, base_url="http://test") as ac:
        yield ac

    del test_app.dependency_overrides[get_session]  # Reset overrides after tests


@pytest.fixture(scope="session")
def celery_settings():
    print(f"{test_celery_settings = }")
    print(f"{test_celery_settings.broker_url = }")
    print(f"{test_celery_settings.result_backend = }")
    return test_celery_settings


@pytest.fixture(scope="session")
def celery_config(settings, celery_settings):
    # these are normally set in lexy.celery_app.create_celery function
    # TODO: add 'lexy.core.celery_tasks' here?
    celery_settings.imports = list(settings.worker_transformer_imports)
    celery_settings.include = settings.worker_transformer_imports

    celery_settings_dict = dict()
    for key in dir(celery_settings):
        if not key.startswith("__"):
            celery_settings_dict[key] = getattr(celery_settings, key)
    print(f"{celery_settings_dict = }")
    return celery_settings_dict


@pytest.fixture(scope="session")
def use_celery_app_trap():
    # throws an error if a test tries to access the default celery app - can override in tests that need it
    #  using `@pytest.mark.usefixtures('depends_on_current_app')`
    return True


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()
