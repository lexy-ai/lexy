import os

import asyncio
import httpx
import pytest
from celery import current_app
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import close_all_sessions
from sqlmodel import SQLModel, create_engine, delete
from sqlmodel.ext.asyncio.session import AsyncSession, AsyncEngine

from lexy.core.config import TestAppSettings
from lexy.db.init_db import add_default_data_to_db, add_first_superuser_to_db
from lexy.db.session import get_session
import lexy.db.session as db_session
from lexy import models


test_settings = TestAppSettings()
DB_WARNING_MSG = "There's a good chance you're about to drop the wrong database! Double check your test settings."
assert test_settings.POSTGRES_DB != "lexy", DB_WARNING_MSG
test_settings.DB_ECHO_LOG = False


# the value of CELERY_CONFIG is set using pytest-env plugin in pyproject.toml
assert os.environ.get("CELERY_CONFIG") == "testing", "CELERY_CONFIG is not set to 'testing'"


def create_test_engine(settings: TestAppSettings = test_settings) -> Engine:
    """Create a SQLAlchemy sync engine for the test database."""
    return create_engine(
        url=settings.sync_database_url,
        echo=settings.DB_ECHO_LOG
    )


test_engine = create_test_engine()
assert test_engine.url.database != "lexy", DB_WARNING_MSG
db_session.get_sync_engine = lambda: test_engine
db_session.sync_engine = test_engine

# in order to work, this has to come after `db_session.get_sync_engine` is overwritten
from lexy.main import app as lexy_test_app  # noqa: E402


# UPDATE: seems like this is no longer needed with the new celery_worker fixture?
#    - https://docs.celeryq.dev/en/stable/userguide/testing.html#celery-worker-embed-live-worker
# NOTE: task_always_eager is ignored when running celery.send_task, one option is to override the send_task method
#  to return the result of the task synchronously. This approach is for integration testing, where we want to test
#  the full flow of the application. It won't work for CI/CD, so we eventually need to move to mocking the celery
#  tasks instead (using pytest-mock). Based on the following sources:
#    - https://stackoverflow.com/a/35807024
#    - https://stackoverflow.com/questions/35284043/mock-celery-task-method-apply-async
#    - https://pytest-with-eric.com/pytest-advanced/mock-celery-task-pytest/
#    - https://stackoverflow.com/questions/72129975/celery-integration-testing-with-pytest-and-monkeypatching
# def send_task(name, args=(), kwargs={}, **opts):
#     # https://github.com/celery/celery/issues/581
#     task = current_app.tasks[name]
#     return task.apply(args, kwargs, **opts)
#
#
# current_app.send_task = send_task


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
        # sync_session.query(model).delete()
        result = local_session.execute(delete(model))
        deleted_count = result.rowcount
        print(f"\tdeleting {deleted_count} {model.__name__} objects")
    local_session.commit()
    close_all_sessions()
    print("Deleted test DB data")


@pytest.fixture(scope="function")
def sync_session(sync_engine, create_test_database):
    """Create a new sync session for each test case."""
    session = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)
    with session() as s:
        yield s


@pytest.fixture(scope="function")
async def async_session(async_engine, seed_data):
    """Create a new async session for each test case."""
    async_session = sessionmaker(
        bind=async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session


@pytest.fixture(scope="session")
def client(seed_data) -> TestClient:
    """Fixture for providing a synchronous TestClient configured for testing."""
    # Override get_session dependency to use the test database session
    lexy_test_app.dependency_overrides[get_session] = lambda: async_session
    print('instantiating TestClient from within client fixture')
    # this next line triggers the `@app.on_startup` event in lexy/main.py
    with TestClient(app=lexy_test_app) as c:
        yield c
    lexy_test_app.dependency_overrides.clear()  # Reset overrides after tests


@pytest.fixture(scope="function")
async def async_client(async_session: AsyncSession) -> httpx.AsyncClient:
    """Fixture for providing an asynchronous TestClient configured for testing."""
    # Override get_session dependency to use the test database session
    lexy_test_app.dependency_overrides[get_session] = lambda: async_session
    print('instantiating Async TestClient from within async_client fixture')
    # this next line does NOT trigger the `@app.on_startup` event in lexy/main.py
    async with httpx.AsyncClient(app=lexy_test_app, base_url="http://test") as ac:
        yield ac
    lexy_test_app.dependency_overrides.clear()  # Reset overrides after tests


@pytest.fixture(scope="session")
def celery_config():
    return current_app.conf


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
