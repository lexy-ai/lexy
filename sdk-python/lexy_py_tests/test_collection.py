import pytest

from lexy_py.client import LexyClient
from lexy_py.collection.models import Collection


class TestCollectionClient:

    def test_root(self, lx_client):
        response = lx_client.get("/")
        assert response.status_code == 200
        assert response.json() == {"Say": "Hello!"}

    def test_collections(self, lx_client):
        collections = lx_client.list_collections()
        assert len(collections) > 0
        collection_names = [collection.collection_id for collection in collections]
        assert "default" in collection_names

        # create test collection
        test_collection = lx_client.create_collection("test_collection", "Test Collection")
        assert test_collection.collection_id == "test_collection"
        assert test_collection.description == "Test Collection"

        # get test collection
        test_collection = lx_client.get_collection("test_collection")
        assert test_collection.collection_id == "test_collection"
        assert test_collection.description == "Test Collection"

        # update test collection
        test_collection = lx_client.update_collection("test_collection", "Test Collection Updated")
        assert test_collection.collection_id == "test_collection"
        assert test_collection.description == "Test Collection Updated"
        assert test_collection.updated_at > test_collection.created_at

        # delete test collection
        response = lx_client.delete_collection("test_collection")
        assert response.get("msg") == "Collection deleted"

    def test_list_collections(self, lx_client):
        collections = lx_client.list_collections()
        assert len(collections) > 0
        collection_ids = [c.collection_id for c in collections]
        assert "default" in collection_ids
        assert isinstance(collections[0].client, LexyClient)

    @pytest.mark.asyncio
    async def test_alist_collections(self, lx_async_client):
        collections = await lx_async_client.collection.alist_collections()
        assert len(collections) > 0
        collection_ids = [c.collection_id for c in collections]
        assert "default" in collection_ids
        assert isinstance(collections[0].client, LexyClient)

    def test_get_collection(self, lx_client):
        collection = lx_client.get_collection("default")
        assert collection.collection_id == "default"
        assert isinstance(collection.client, LexyClient)

    @pytest.mark.asyncio
    async def test_aget_collection(self, lx_async_client):
        collection = await lx_async_client.collection.aget_collection("default")
        assert collection.collection_id == "default"
        assert isinstance(collection.client, LexyClient)

    def test_collection_client(self):
        collection_without_a_client = Collection(collection_id="no_client", description="No client")
        with pytest.raises(ValueError) as exc_info:
            collection_without_a_client.list_documents()
        assert isinstance(exc_info.value, ValueError)
        assert str(exc_info.value) == "API client has not been set."
