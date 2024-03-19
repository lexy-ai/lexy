import pytest

from lexy_py.client import LexyClient
from lexy_py.exceptions import LexyAPIError
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
        assert response == {
            "msg": "Collection deleted",
            "collection_id": "test_collection",
            "documents_deleted": 0
        }, response

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

    def test_create_existing_collection(self, lx_client):
        with pytest.raises(LexyAPIError) as exc_info:
            lx_client.create_collection("default", "Default Collection")
        assert isinstance(exc_info.value, LexyAPIError)
        assert exc_info.value.response_data["status_code"] == 400, exc_info.value.response_data
        assert exc_info.value.response.status_code == 400
        assert exc_info.value.response.json()["detail"] == "Collection with that ID already exists"

    def test_delete_collection(self, lx_client):
        # create test collection
        test_collection = lx_client.create_collection("test_collection", "Test Collection")
        assert test_collection.collection_id == "test_collection"
        assert test_collection.description == "Test Collection"

        # add docs to test collection
        docs_added = lx_client.add_documents([
            {"content": "Test Document 1 Content"},
            {"content": "Test Document 2 Content"}
        ], collection_id="test_collection")
        assert docs_added[0].collection_id == "test_collection"
        assert docs_added[1].collection_id == "test_collection"
        assert docs_added[0].document_id is not None
        assert docs_added[0].created_at is not None
        assert docs_added[0].collection_id == "test_collection"

        # try to delete test collection with documents
        with pytest.raises(LexyAPIError) as exc_info:
            lx_client.delete_collection("test_collection")
        assert isinstance(exc_info.value, LexyAPIError)
        assert exc_info.value.response_data["status_code"] == 400, exc_info.value.response_data
        assert exc_info.value.response.status_code == 400
        assert exc_info.value.response.json()["detail"] == ("There are still documents in this collection. "
                                                            "Set delete_documents=True to delete them.")

        # delete test collection
        response = lx_client.delete_collection("test_collection", delete_documents=True)
        assert response == {
            "msg": "Collection deleted",
            "collection_id": "test_collection",
            "documents_deleted": 2
        }, response


class TestCollectionModel:

    def test_collection_model(self):
        collection = Collection(collection_id="test_collection", description="Test Collection")
        assert collection.collection_id == "test_collection"
        assert collection.description == "Test Collection"

    def test_collection_without_client(self):
        collection_without_a_client = Collection(collection_id="no_client", description="No client")
        with pytest.raises(ValueError) as exc_info:
            collection_without_a_client.list_documents()
        assert isinstance(exc_info.value, ValueError)
        assert str(exc_info.value) == "API client has not been set."
