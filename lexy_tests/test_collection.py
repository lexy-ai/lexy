import pytest
from sqlmodel import select

from lexy.models.collection import Collection, CollectionCreate, CollectionUpdate


class TestCollection:
    def test_hello(self):
        assert True

    @pytest.mark.asyncio
    async def test_get_collections(self, async_session):
        result = await async_session.exec(select(Collection))
        collections = result.all()
        assert len(collections) > 1
        collection_names = [c.collection_name for c in collections]
        assert "default" in collection_names

    def test_get_collections_with_client(self, client):
        response = client.get(
            "/api/collections",
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert len(data) > 1
        collection_names = [c["collection_name"] for c in data]
        assert "default" in collection_names

    @pytest.mark.asyncio
    async def test_get_collections_with_async_client(self, async_client):
        response = await async_client.get(
            "/api/collections",
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert len(data) > 1
        collection_names = [c["collection_name"] for c in data]
        assert "default" in collection_names

    @pytest.mark.asyncio
    async def test_create_collection(self, async_session, settings):
        collection = Collection(
            collection_name="test_collection", description="Test Collection"
        )
        async_session.add(collection)
        await async_session.commit()
        await async_session.refresh(collection)
        assert collection.collection_id is not None
        assert collection.collection_name == "test_collection"
        assert collection.description == "Test Collection"
        assert collection.config == settings.COLLECTION_DEFAULT_CONFIG
        assert collection.created_at is not None
        assert collection.updated_at is not None

        result = await async_session.exec(
            select(Collection).where(Collection.collection_name == "test_collection")
        )
        collections = result.all()
        assert len(collections) == 1
        assert collections[0].collection_name == "test_collection"
        assert collections[0].description == "Test Collection"
        assert collections[0].config == settings.COLLECTION_DEFAULT_CONFIG

    @pytest.mark.asyncio
    async def test_create_collection_with_model_validate(self, async_session, settings):
        collection = CollectionCreate(
            collection_name="test_collection_validated",
            description="Test Collection Validated",
        )
        assert collection.collection_name == "test_collection_validated"
        assert collection.description == "Test Collection Validated"
        assert collection.config == settings.COLLECTION_DEFAULT_CONFIG

        db_collection = Collection.model_validate(collection)
        async_session.add(db_collection)
        await async_session.commit()
        await async_session.refresh(db_collection)
        assert db_collection.collection_id is not None
        assert db_collection.collection_name == "test_collection_validated"
        assert db_collection.description == "Test Collection Validated"
        assert db_collection.config == settings.COLLECTION_DEFAULT_CONFIG
        assert db_collection.created_at is not None
        assert db_collection.updated_at is not None

        result = await async_session.exec(
            select(Collection).where(
                Collection.collection_name == "test_collection_validated"
            )
        )
        collections = result.all()
        assert len(collections) == 1
        assert collections[0].collection_name == "test_collection_validated"
        assert collections[0].description == "Test Collection Validated"
        assert collections[0].config == settings.COLLECTION_DEFAULT_CONFIG

    @pytest.mark.asyncio
    async def test_collection_crud(self, async_session):
        # create collection
        collection = CollectionCreate(
            collection_name="test_collection_crud", description="Test Collection CRUD"
        )
        db_collection = Collection.model_validate(collection)
        async_session.add(db_collection)
        await async_session.commit()
        await async_session.refresh(db_collection)
        assert db_collection.collection_id is not None
        assert db_collection.collection_name == "test_collection_crud"
        assert db_collection.description == "Test Collection CRUD"
        assert db_collection.created_at is not None
        assert db_collection.updated_at is not None

        # get collection
        result = await async_session.exec(
            select(Collection).where(
                Collection.collection_name == "test_collection_crud"
            )
        )
        collections = result.all()
        assert len(collections) == 1
        assert collections[0].collection_name == "test_collection_crud"
        assert collections[0].description == "Test Collection CRUD"

        # update collection
        collection_update = CollectionUpdate(description="Test Collection CRUD Updated")
        collection_data = collection_update.model_dump(exclude_unset=True)
        for key, value in collection_data.items():
            setattr(db_collection, key, value)
        async_session.add(db_collection)
        await async_session.commit()
        await async_session.refresh(db_collection)
        assert db_collection.collection_id is not None
        assert db_collection.collection_name == "test_collection_crud"
        assert db_collection.description == "Test Collection CRUD Updated"
        assert db_collection.created_at is not None
        assert db_collection.updated_at > db_collection.created_at

        # delete collection
        result = await async_session.exec(
            select(Collection).where(
                Collection.collection_name == "test_collection_crud"
            )
        )
        collection = result.first()
        assert collection is not None
        await async_session.delete(collection)
        await async_session.commit()

        result = await async_session.exec(
            select(Collection).where(
                Collection.collection_name == "test_collection_crud"
            )
        )
        collection = result.first()
        assert collection is None


class TestCollectionModel:
    def test_create_collection_model(self):
        collection = CollectionCreate(collection_name="test_collection")
        assert collection.collection_name == "test_collection"
        collection = CollectionCreate(collection_name="_te5t")
        assert collection.collection_name == "_te5t"
        collection = CollectionCreate(collection_name="_mytable" * 7)
        assert collection.collection_name == "_mytable" * 7

    def test_create_collection_model_with_invalid_name(self):
        with pytest.raises(ValueError):
            CollectionCreate(collection_name="", description="Test Collection")  # blank
        with pytest.raises(ValueError):
            CollectionCreate(
                collection_name="test collection", description="Test Collection"
            )  # space
        with pytest.raises(ValueError):
            CollectionCreate(
                collection_name="test-collection", description="Test Collection"
            )  # hyphen
        with pytest.raises(ValueError):
            CollectionCreate(
                collection_name="Test", description="Test Collection"
            )  # uppercase
        with pytest.raises(ValueError):
            CollectionCreate(
                collection_name="1abc", description="Test Collection"
            )  # starts with number
        with pytest.raises(ValueError):
            CollectionCreate(
                collection_name="_mytable" * 8, description="Test Collection"
            )  # too long

    def test_update_collection_model(self):
        collection_update = CollectionUpdate(collection_name="test_collection")
        assert collection_update.collection_name == "test_collection"
        collection_update = CollectionUpdate(
            collection_name="_te5t", description="Updated description"
        )
        assert collection_update.collection_name == "_te5t"
        assert collection_update.description == "Updated description"
        collection_update = CollectionUpdate(description="Updated description")
        assert collection_update.collection_name is None
        assert collection_update.description == "Updated description"

    def test_update_collection_model_with_invalid_name(self):
        with pytest.raises(ValueError):
            CollectionUpdate(collection_name="", description="Test Collection")  # blank
        with pytest.raises(ValueError):
            CollectionUpdate(
                collection_name="test collection", description="Test Collection"
            )  # space
        with pytest.raises(ValueError):
            CollectionUpdate(
                collection_name="test-collection", description="Test Collection"
            )  # hyphen
        with pytest.raises(ValueError):
            CollectionUpdate(
                collection_name="Test", description="Test Collection"
            )  # uppercase
        with pytest.raises(ValueError):
            CollectionUpdate(
                collection_name="1abc", description="Test Collection"
            )  # starts with number
        with pytest.raises(ValueError):
            CollectionUpdate(
                collection_name="_mytable" * 8, description="Test Collection"
            )  # too long
