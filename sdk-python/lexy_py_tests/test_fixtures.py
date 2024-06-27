import pytest


class TestFixtures:
    """Test the fixtures in `sdk-python/lexy_py_tests/conftest.py`."""

    def test_hello(self):
        assert True

    def test_get_root_with_lx_client(self, lx_client):
        response = lx_client.client.get("/")
        assert response.status_code == 200
        assert response.json() == {"Say": "Hello!"}

    @pytest.mark.asyncio
    async def test_get_root_with_lx_client(self, lx_client):  # noqa: F811
        response = lx_client.client.get("/")
        assert response.status_code == 200
        assert response.json() == {"Say": "Hello!"}

    @pytest.mark.asyncio
    async def test_get_root_with_lx_async_client(self, lx_async_client):
        response = await lx_async_client.aclient.get(
            "/",  # trailing slash is required on the root path only - https://stackoverflow.com/a/70354027
        )
        assert response.status_code == 200
        assert response.json() == {"Say": "Hello!"}

    def test_get_ping_with_lx_client(self, lx_client):
        response = lx_client.get(
            "/ping",
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data == {"ping": "pong!"}

    @pytest.mark.asyncio
    async def test_get_ping_with_lx_client(self, lx_client):  # noqa: F811
        response = lx_client.get(
            "/ping",
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data == {"ping": "pong!"}

    @pytest.mark.asyncio
    async def test_get_ping_with_lx_async_client(self, lx_async_client):
        response = await lx_async_client.aget(
            "/ping",
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data == {"ping": "pong!"}

    def test_get_db_endpoint_with_lx_client(self, lx_client):
        response = lx_client.get(
            "/collections",
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert len(data) > 1

    @pytest.mark.asyncio
    async def test_get_db_endpoint_with_lx_client(self, lx_client):  # noqa: F811
        response = lx_client.get(
            "/collections",
        )
        assert response.status_code == 200, response.text
        data = response.json()
        print(f"{data = }")
        assert len(data) > 1

    @pytest.mark.asyncio
    async def test_get_db_endpoint_with_lx_async_client(self, lx_async_client):
        response = await lx_async_client.aget(
            "/collections",
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert len(data) > 1
