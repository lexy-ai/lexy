import os

import asyncio
import httpx
import pytest
from fastapi.testclient import TestClient

from lexy_tests.conftest import (
    async_client,
    async_engine,
    async_session,
    celery_config,
    client,
    create_test_database,
    create_test_engine,
    get_session,
    seed_data,
    settings,
    sync_engine,
    test_app,
    test_engine,
    test_settings,
    use_celery_app_trap,
)
from lexy_py import LexyClient


DB_WARNING_MSG = "There's a good chance you're about to drop the wrong database! Double check your test settings."
assert test_settings.POSTGRES_DB != "lexy", DB_WARNING_MSG
test_settings.DB_ECHO_LOG = False

# the value of CELERY_CONFIG is set using pytest-env plugin in pyproject.toml
assert os.environ.get("CELERY_CONFIG") == "testing", "CELERY_CONFIG is not set to 'testing'"

TEST_BASE_URL = "http://test"
TEST_API_TIMEOUT = 10


@pytest.fixture(scope="function")
def lx_client(client: TestClient) -> LexyClient:
    """Create a new Lexy client instance for each synchronous test case."""
    with LexyClient(base_url=TEST_BASE_URL, api_timeout=TEST_API_TIMEOUT) as lxs:
        lxs.client = client
        # append the API_PREFIX (e.g., "/api") to the base_url
        lxs.client.base_url = lxs.client.base_url.join(test_settings.API_PREFIX)
        lxs.aclient = None
        yield lxs


@pytest.fixture(scope="function")
async def lx_async_client(async_client: httpx.AsyncClient) -> LexyClient:
    """Create a new Lexy client instance for each asynchronous test case."""
    async with LexyClient(base_url=TEST_BASE_URL, api_timeout=TEST_API_TIMEOUT) as lxa:
        lxa.client = None
        lxa.aclient = async_client
        # append the API_PREFIX (e.g., "/api") to the base_url
        lxa.aclient.base_url = lxa.aclient.base_url.join(test_settings.API_PREFIX)
        yield lxa


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()
