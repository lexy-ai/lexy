import pytest
from sqlmodel import select

from lexy.models.collection import Collection


class TestCollection:

    def test_hello(self):
        assert True

    @pytest.mark.asyncio
    async def test_get_collections(self, async_session):
        result = await async_session.exec(select(Collection))
        collections = result.all()
        assert len(collections) > 1
        collection_ids = [c.collection_id for c in collections]
        assert "default" in collection_ids

    def test_get_collections_with_client(self, client):
        response = client.get(
            "/api/collections",
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert len(data) > 1
        collection_ids = [c['collection_id'] for c in data]
        assert "default" in collection_ids

    @pytest.mark.asyncio
    async def test_get_collections_with_async_client(self, async_client):
        response = await async_client.get(
            "/api/collections",
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert len(data) > 1
        collection_ids = [c['collection_id'] for c in data]
        assert "default" in collection_ids

    @pytest.mark.asyncio
    async def test_create_collection(self, async_session):
        collection = Collection(collection_id="test_collection", description="Test Collection")
        async_session.add(collection)
        await async_session.commit()
        await async_session.refresh(collection)
        assert collection.collection_id == "test_collection"
        assert collection.description == "Test Collection"
        assert collection.created_at is not None
        assert collection.updated_at is not None

        result = await async_session.exec(select(Collection).where(Collection.collection_id == "test_collection"))
        collections = result.all()
        assert len(collections) == 1
        assert collections[0].collection_id == "test_collection"
        assert collections[0].description == "Test Collection"
