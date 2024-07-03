import pytest


class TestFixtures:
    """Test the fixtures in `lexy_tests/conftest.py`."""

    def test_hello(self):
        assert True

    def test_get_root_with_client(self, client):
        response = client.get("/api")
        assert response.status_code == 200
        assert response.json() == {"Say": "Hello!"}

    @pytest.mark.asyncio
    async def test_get_root_with_client(self, client):  # noqa: F811
        response = client.get("/api")
        assert response.status_code == 200
        assert response.json() == {"Say": "Hello!"}

    @pytest.mark.asyncio
    async def test_get_root_with_async_client(self, async_client):
        response = await async_client.get(
            # Trailing slash is required on the root path only.
            # See https://stackoverflow.com/a/70354027
            "/api/",
        )
        assert response.status_code == 200
        assert response.json() == {"Say": "Hello!"}

    def test_get_ping_with_client(self, client):
        response = client.get(
            "/api/ping",
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data == {"ping": "pong!"}

    @pytest.mark.asyncio
    async def test_get_ping_with_client(self, client):  # noqa: F811
        response = client.get(
            "/api/ping",
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data == {"ping": "pong!"}

    @pytest.mark.asyncio
    async def test_get_ping_with_async_client(self, async_client):
        response = await async_client.get(
            "/api/ping",
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data == {"ping": "pong!"}

    def test_get_db_endpoint_with_client(self, client):
        response = client.get(
            "/api/collections",
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert len(data) > 1

    @pytest.mark.asyncio
    async def test_get_db_endpoint_with_client(self, client):  # noqa: F811
        response = client.get(
            "/api/collections",
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert len(data) > 1

    @pytest.mark.asyncio
    async def test_get_db_endpoint_with_async_client(self, async_client):
        response = await async_client.get(
            "/api/collections",
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert len(data) > 1
