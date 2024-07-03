import pytest

from lexy_py.client import LexyClient
from lexy_py.exceptions import LexyAPIError
from lexy_py.collection.models import Collection, CollectionUpdate


class TestCollectionClient:
    def test_root(self, lx_client):
        response = lx_client.get("/")
        assert response.status_code == 200
        assert response.json() == {"Say": "Hello!"}

    def test_collections(self, lx_client):
        collections = lx_client.list_collections()
        assert len(collections) > 0
        collection_names = [collection.collection_name for collection in collections]
        assert "default" in collection_names

        # create test collection
        test_collection = lx_client.create_collection(
            "test_collection", description="Test Collection"
        )
        test_collection_id = test_collection.collection_id
        assert test_collection_id is not None
        assert test_collection.collection_name == "test_collection"
        assert test_collection.description == "Test Collection"

        # get test collection
        test_collection = lx_client.get_collection(collection_name="test_collection")
        assert test_collection.collection_id == test_collection_id
        assert test_collection.collection_name == "test_collection"
        assert test_collection.description == "Test Collection"

        # update test collection
        test_collection = lx_client.update_collection(
            collection_id=test_collection_id, description="Test Collection Updated"
        )
        assert test_collection.collection_name == "test_collection"
        assert test_collection.description == "Test Collection Updated"
        assert test_collection.updated_at > test_collection.created_at

        # update test collection name
        test_collection = lx_client.update_collection(
            collection_id=test_collection_id, collection_name="test_collection_updated"
        )
        assert test_collection.collection_name == "test_collection_updated"
        assert test_collection.description == "Test Collection Updated"
        assert test_collection.updated_at > test_collection.created_at

        # delete test collection
        response = lx_client.delete_collection(
            collection_name="test_collection_updated"
        )
        assert response == {
            "msg": "Collection deleted",
            "collection_id": test_collection_id,
            "documents_deleted": 0,
        }, response

    def test_list_collections(self, lx_client):
        collections = lx_client.list_collections()
        assert len(collections) > 0
        collection_names = [c.collection_name for c in collections]
        assert "default" in collection_names
        assert isinstance(collections[0].client, LexyClient)

    @pytest.mark.asyncio
    async def test_alist_collections(self, lx_async_client):
        collections = await lx_async_client.collection.alist_collections()
        assert len(collections) > 0
        collection_names = [c.collection_name for c in collections]
        assert "default" in collection_names
        assert isinstance(collections[0].client, LexyClient)

    def test_get_collection(self, lx_client):
        collection = lx_client.get_collection(collection_name="default")
        assert collection.collection_name == "default"
        assert isinstance(collection.client, LexyClient)
        collection_by_id = lx_client.get_collection(
            collection_id=collection.collection_id
        )
        assert collection_by_id.collection_name == "default"
        assert isinstance(collection_by_id.client, LexyClient)

    @pytest.mark.asyncio
    async def test_aget_collection(self, lx_async_client):
        collection = await lx_async_client.collection.aget_collection(
            collection_name="default"
        )
        assert collection.collection_name == "default"
        assert isinstance(collection.client, LexyClient)
        collection_by_id = await lx_async_client.collection.aget_collection(
            collection_id=collection.collection_id
        )
        assert collection_by_id.collection_name == "default"
        assert isinstance(collection_by_id.client, LexyClient)

    def test_create_existing_collection(self, lx_client):
        with pytest.raises(LexyAPIError) as exc_info:
            lx_client.create_collection("default", description="Default Collection")
        assert isinstance(exc_info.value, LexyAPIError)
        assert (
            exc_info.value.response_data["status_code"] == 400
        ), exc_info.value.response_data
        assert exc_info.value.response.status_code == 400
        assert (
            exc_info.value.response.json()["detail"]
            == "Collection with that name already exists"
        )

    def test_delete_collection(self, lx_client):
        # create test collection
        test_collection = lx_client.create_collection(
            "test_delete_collection", description="Test Collection"
        )
        assert test_collection.collection_name == "test_delete_collection"
        assert test_collection.description == "Test Collection"

        # add docs to test collection
        docs_added = lx_client.add_documents(
            [
                {"content": "Test Document 1 Content"},
                {"content": "Test Document 2 Content"},
            ],
            collection_id=test_collection.collection_id,
        )
        assert docs_added[0].collection_id == test_collection.collection_id
        assert docs_added[1].collection_id == test_collection.collection_id
        assert docs_added[0].document_id is not None
        assert docs_added[0].created_at is not None

        # try to delete test collection with documents
        with pytest.raises(LexyAPIError) as exc_info:
            lx_client.delete_collection(collection_name="test_delete_collection")
        assert isinstance(exc_info.value, LexyAPIError)
        assert (
            exc_info.value.response_data["status_code"] == 400
        ), exc_info.value.response_data
        assert exc_info.value.response.status_code == 400
        assert exc_info.value.response.json()["detail"] == (
            "There are still documents in this collection. "
            "Set delete_documents=True to delete them."
        )

        # delete test collection
        response = lx_client.delete_collection(
            collection_name="test_delete_collection", delete_documents=True
        )
        assert response == {
            "msg": "Collection deleted",
            "collection_id": test_collection.collection_id,
            "documents_deleted": 2,
        }, response

    def test_delete_nonexistent_collection(self, lx_client):
        with pytest.raises(LexyAPIError) as exc_info:
            lx_client.delete_collection(collection_name="nonexistent_collection")
        assert isinstance(exc_info.value, LexyAPIError)
        assert (
            exc_info.value.response_data["status_code"] == 404
        ), exc_info.value.response_data
        assert exc_info.value.response.status_code == 404
        assert exc_info.value.response.json()["detail"] == "Collection not found"

    def test_update_collection(self, lx_client):
        # create test collection
        test_collection = lx_client.create_collection(
            "test_update_collection", description="Test Update Collection"
        )
        test_collection_id = test_collection.collection_id
        assert test_collection_id is not None
        assert test_collection.collection_name == "test_update_collection"
        assert test_collection.description == "Test Update Collection"

        # update to collection name that already exists (should fail)
        with pytest.raises(LexyAPIError) as exc_info:
            lx_client.update_collection(
                collection_id=test_collection_id, collection_name="default"
            )
        assert isinstance(exc_info.value, LexyAPIError)
        assert (
            exc_info.value.response_data["status_code"] == 400
        ), exc_info.value.response_data
        assert exc_info.value.response.status_code == 400
        assert (
            exc_info.value.response.json()["detail"]
            == "Collection with that name already exists"
        )

        # Update to invalid collection name '1abc' (should fail) - currently fails via
        # the client
        with pytest.raises(ValueError) as exc_info:
            lx_client.update_collection(
                collection_id=test_collection_id, collection_name="1abc"
            )

        # check that the collection was not updated
        test_collection = lx_client.get_collection(
            collection_name="test_update_collection"
        )
        assert test_collection.collection_id == test_collection_id
        assert test_collection.collection_name == "test_update_collection"
        assert test_collection.description == "Test Update Collection"
        assert test_collection.updated_at == test_collection.created_at

        # update collection description
        test_collection = lx_client.update_collection(
            collection_id=test_collection_id, description="A brand new description"
        )
        assert test_collection.collection_id == test_collection_id
        assert test_collection.collection_name == "test_update_collection"
        assert test_collection.description == "A brand new description"
        assert test_collection.updated_at > test_collection.created_at
        test_collection_updated_at = test_collection.updated_at

        # update collection name
        test_collection = lx_client.update_collection(
            collection_id=test_collection_id,
            collection_name="test_update_collection_updated",
        )
        assert test_collection.collection_id == test_collection_id
        assert test_collection.collection_name == "test_update_collection_updated"
        assert test_collection.description == "A brand new description"
        assert test_collection.updated_at > test_collection_updated_at

        # delete collection
        response = lx_client.delete_collection(
            collection_name="test_update_collection_updated"
        )
        assert response == {
            "msg": "Collection deleted",
            "collection_id": test_collection_id,
            "documents_deleted": 0,
        }, response


class TestCollectionModel:
    def test_collection_model(self):
        collection = Collection(
            collection_name="test_collection", description="Test Collection"
        )
        assert collection.collection_id is None
        assert collection.collection_name == "test_collection"
        assert collection.description == "Test Collection"

    def test_collection_without_client(self):
        collection_without_a_client = Collection(
            collection_name="no_client", description="No client"
        )
        with pytest.raises(ValueError) as exc_info:
            collection_without_a_client.list_documents()
        assert isinstance(exc_info.value, ValueError)
        assert str(exc_info.value) == "API client has not been set."

    def test_create_collection(self):
        collection = Collection(collection_name="test_collection")
        assert collection.collection_name == "test_collection"
        collection = Collection(collection_name="_te5t")
        assert collection.collection_name == "_te5t"
        collection = Collection(collection_name="_mytable" * 7)
        assert collection.collection_name == "_mytable" * 7

    def test_create_collection_with_invalid_name(self):
        with pytest.raises(ValueError):
            Collection(collection_name="", description="Test Collection")  # blank
        with pytest.raises(ValueError):
            Collection(
                collection_name="test collection", description="Test Collection"
            )  # space
        with pytest.raises(ValueError):
            Collection(
                collection_name="test-collection", description="Test Collection"
            )  # hyphen
        with pytest.raises(ValueError):
            Collection(
                collection_name="Test", description="Test Collection"
            )  # uppercase
        with pytest.raises(ValueError):
            Collection(
                collection_name="1abc", description="Test Collection"
            )  # starts with number
        with pytest.raises(ValueError):
            Collection(
                collection_name="_mytable" * 8, description="Test Collection"
            )  # too long

    def test_update_collection(self):
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

    def test_update_collection_with_invalid_name(self):
        with pytest.raises(ValueError):
            CollectionUpdate(collection_name="", description="Test Collection")
        with pytest.raises(ValueError):
            CollectionUpdate(
                collection_name="test collection", description="Test Collection"
            )
        with pytest.raises(ValueError):
            CollectionUpdate(
                collection_name="test-collection", description="Test Collection"
            )
        with pytest.raises(ValueError):
            CollectionUpdate(collection_name="Test", description="Test Collection")
        with pytest.raises(ValueError):
            CollectionUpdate(collection_name="1abc", description="Test Collection")
        with pytest.raises(ValueError):
            CollectionUpdate(
                collection_name="_mytable" * 8, description="Test Collection"
            )
