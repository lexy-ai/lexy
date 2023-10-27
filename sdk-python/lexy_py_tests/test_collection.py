import pytest

from lexy_py.client import LexyClient


lexy = LexyClient()


class TestCollectionClient:

    def test_root(self):
        response = lexy.get("/")
        assert response.status_code == 200
        assert response.json() == {"Say": "Hello!"}

    def test_collections(self):
        collections = lexy.collection.list_collections()
        assert len(collections) > 0
        assert collections[0].collection_id == "default"

        # create test collection
        test_collection = lexy.collection.add_collection("test_collection", "Test Collection")
        assert test_collection.collection_id == "test_collection"
        assert test_collection.description == "Test Collection"

        # get test collection
        test_collection = lexy.collection.get_collection("test_collection")
        assert test_collection.collection_id == "test_collection"
        assert test_collection.description == "Test Collection"

        # update test collection
        test_collection = lexy.collection.update_collection("test_collection", "Test Collection Updated")
        assert test_collection.collection_id == "test_collection"
        assert test_collection.description == "Test Collection Updated"
        assert test_collection.updated_at > test_collection.created_at

        # delete test collection
        response = lexy.collection.delete_collection("test_collection")
        assert response == {"Say": "Collection deleted!"}

    def test_list_collections(self):
        collections = lexy.collection.list_collections()
        assert len(collections) > 0
        assert collections[0].collection_id == "default"

    @pytest.mark.asyncio
    async def test_alist_collections(self):
        collections = await lexy.collection.alist_collections()
        assert len(collections) > 0
        assert collections[0].collection_id == "default"

    def test_get_collection(self):
        collection = lexy.collection.get_collection("default")
        assert collection.collection_id == "default"

    @pytest.mark.asyncio
    async def test_aget_collection(self):
        collection = await lexy.collection.aget_collection("default")
        assert collection.collection_id == "default"
