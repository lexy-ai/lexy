import pytest
from sqlmodel import select

from lexy.models.collection import Collection, CollectionCreate


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

        result = await async_session.exec(
            select(Collection).where(Collection.collection_id == "test_collection")
        )
        collections = result.all()
        assert len(collections) == 1
        assert collections[0].collection_id == "test_collection"
        assert collections[0].description == "Test Collection"

    @pytest.mark.asyncio
    async def test_create_collection_with_model_validate(self, async_session):
        collection = CollectionCreate(
            collection_id="test_collection_validated", description="Test Collection Validated"
        )

        db_collection = Collection.model_validate(collection)
        async_session.add(db_collection)
        await async_session.commit()
        await async_session.refresh(db_collection)
        assert db_collection.collection_id == "test_collection_validated"
        assert db_collection.description == "Test Collection Validated"
        assert db_collection.created_at is not None
        assert db_collection.updated_at is not None

        result = await async_session.exec(
            select(Collection).where(Collection.collection_id == "test_collection_validated")
        )
        collections = result.all()
        assert len(collections) == 1
        assert collections[0].collection_id == "test_collection_validated"
        assert collections[0].description == "Test Collection Validated"


class TestCollectionModel:

    def test_create_collection(self):
        collection = CollectionCreate(collection_id="test_collection")
        assert collection.collection_id == "test_collection"
        collection = CollectionCreate(collection_id="_te5t")
        assert collection.collection_id == "_te5t"
        collection = CollectionCreate(collection_id="_mytable" * 7)
        assert collection.collection_id == "_mytable" * 7

    def test_create_collection_with_invalid_id(self):
        with pytest.raises(ValueError):
            CollectionCreate(collection_id="", description="Test Collection")  # blank
        with pytest.raises(ValueError):
            CollectionCreate(collection_id="test collection", description="Test Collection")  # space
        with pytest.raises(ValueError):
            CollectionCreate(collection_id="test-collection", description="Test Collection")  # hyphen
        with pytest.raises(ValueError):
            CollectionCreate(collection_id="Test", description="Test Collection")  # uppercase
        with pytest.raises(ValueError):
            CollectionCreate(collection_id="1abc", description="Test Collection")  # starts with number
        with pytest.raises(ValueError):
            CollectionCreate(collection_id="_mytable" * 8, description="Test Collection")  # too long
