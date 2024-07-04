import pytest

from lexy_py.client import LexyClient
from lexy_py.binding.models import BindingCreate, BindingUpdate
from lexy_py.collection.models import Collection
from lexy_py.exceptions import LexyAPIError
from lexy_py.filters import FilterBuilder
from lexy_py.index.models import Index
from lexy_py.transformer.models import Transformer


class TestBindingClient:
    def test_root(self, lx_client):
        response = lx_client.get("/")
        assert response.status_code == 200
        assert response.json() == {"Say": "Hello!"}

    def test_list_bindings(self, lx_client):
        bindings = lx_client.list_bindings()
        assert len(bindings) > 0

    @pytest.mark.asyncio
    async def test_alist_bindings(self, lx_async_client):
        bindings = await lx_async_client.binding.alist_bindings()
        assert len(bindings) > 0

    def test_get_binding(self, lx_client):
        binding = lx_client.get_binding(binding_id=1)
        assert binding.binding_id == 1
        assert isinstance(binding.client, LexyClient)

        assert isinstance(binding.collection, Collection)
        assert binding.collection.collection_name == "default"
        assert isinstance(binding.collection.client, LexyClient)

        assert isinstance(binding.index, Index)
        assert binding.index.index_id == "default_text_embeddings"
        assert isinstance(binding.index.client, LexyClient)

        assert isinstance(binding.transformer, Transformer)
        assert binding.transformer.transformer_id == "text.embeddings.minilm"
        assert isinstance(binding.transformer.client, LexyClient)

    @pytest.mark.asyncio
    async def test_aget_binding(self, lx_async_client):
        binding = await lx_async_client.binding.aget_binding(binding_id=1)
        assert binding.binding_id == 1
        assert isinstance(binding.client, LexyClient)

        assert isinstance(binding.collection, Collection)
        assert binding.collection.collection_name == "default"
        assert isinstance(binding.collection.client, LexyClient)

        assert isinstance(binding.index, Index)
        assert binding.index.index_id == "default_text_embeddings"
        assert isinstance(binding.index.client, LexyClient)

        assert isinstance(binding.transformer, Transformer)
        assert binding.transformer.transformer_id == "text.embeddings.minilm"
        assert isinstance(binding.transformer.client, LexyClient)

    def test_create_binding(self, lx_client, celery_app, celery_worker):
        binding = lx_client.create_binding(
            collection_name="default",
            index_id="default_text_embeddings",
            transformer_id="text.embeddings.minilm",
            description="Test Binding",
        )
        assert binding.binding_id is not None
        assert binding.collection.collection_name == "default"
        assert binding.index.index_id == "default_text_embeddings"
        assert binding.transformer.transformer_id == "text.embeddings.minilm"
        assert binding.description == "Test Binding"
        assert binding.status == "on"
        assert "lexy_index_fields" in binding.transformer_params
        assert set(binding.index.index_fields.keys()) == set(
            binding.transformer_params["lexy_index_fields"]
        )

        # delete test binding
        response = lx_client.delete_binding(binding_id=binding.binding_id)
        assert response == {"msg": "Binding deleted", "binding_id": binding.binding_id}

    def test_update_binding_with_filter(self, lx_client, celery_app, celery_worker):
        binding = lx_client.create_binding(
            collection_name="default",
            index_id="default_text_embeddings",
            transformer_id="text.embeddings.minilm",
            description="Test Binding",
        )
        assert binding.binding_id is not None
        assert binding.collection.collection_name == "default"
        assert binding.index.index_id == "default_text_embeddings"
        assert binding.transformer.transformer_id == "text.embeddings.minilm"
        assert binding.description == "Test Binding"
        assert binding.status == "on"
        assert binding.created_at is not None
        assert binding.updated_at is not None
        assert "lexy_index_fields" in binding.transformer_params
        assert set(binding.index.index_fields.keys()) == set(
            binding.transformer_params["lexy_index_fields"]
        )
        assert binding.filter is None

        # create filter
        my_filter = (
            FilterBuilder()
            .include("meta.size", "less_than", 30000)
            .exclude("meta.type", "in", ["image", "video"])
        )

        # update binding description and filter
        binding = lx_client.update_binding(
            binding_id=binding.binding_id,
            description="Test Binding with Filter",
            filters=my_filter,
        )
        assert binding.binding_id is not None
        assert binding.description == "Test Binding with Filter"
        assert binding.filter is not None
        assert binding.filter == my_filter.to_dict()
        assert binding.updated_at > binding.created_at

        # delete test binding
        response = lx_client.delete_binding(binding_id=binding.binding_id)
        assert response == {"msg": "Binding deleted", "binding_id": binding.binding_id}

    def test_create_binding_with_invalid_filter(
        self, lx_client, celery_app, celery_worker
    ):
        # create filter with invalid conditions
        my_filter = FilterBuilder().include("meta.size", "less_than", "hello")

        with pytest.raises(LexyAPIError) as exc_info:
            lx_client.create_binding(
                collection_id="default",
                index_id="default_text_embeddings",
                transformer_id="text.embeddings.minilm",
                description="Test Binding with Invalid Filter",
                filters=my_filter,
            )
        assert isinstance(exc_info.value, LexyAPIError)
        assert (
            exc_info.value.response_data["status_code"] == 422
        ), exc_info.value.response_data
        assert exc_info.value.response.status_code == 422
        assert len(exc_info.value.response.json()["detail"]) == 1
        error = exc_info.value.response.json()["detail"][0]
        assert error["type"] == "value_error"
        assert error["loc"] == ["body", "filter", "conditions", 0, "value"]
        assert (
            error["msg"]
            == "Value error, Value must be a number for operation 'less_than'"
        )
        assert error["input"] == "hello"

    def test_create_binding_with_nonexistent_collection(
        self, lx_client, celery_app, celery_worker
    ):
        with pytest.raises(LexyAPIError) as exc_info:
            lx_client.create_binding(
                collection_name="nonexistent_collection",
                index_id="default_text_embeddings",
                transformer_id="text.embeddings.minilm",
                description="Test Binding with Nonexistent Collection",
            )
        assert isinstance(exc_info.value, LexyAPIError)
        assert (
            exc_info.value.response_data["status_code"] == 400
        ), exc_info.value.response_data
        assert exc_info.value.response.status_code == 400
        assert exc_info.value.response.json()["detail"] == "Collection not found"

    def test_create_binding_with_nonexistent_index(
        self, lx_client, celery_app, celery_worker
    ):
        with pytest.raises(LexyAPIError) as exc_info:
            lx_client.create_binding(
                collection_name="default",
                index_id="nonexistent_index",
                transformer_id="text.embeddings.minilm",
                description="Test Binding with Nonexistent Index",
            )
        assert isinstance(exc_info.value, LexyAPIError)
        assert (
            exc_info.value.response_data["status_code"] == 400
        ), exc_info.value.response_data
        assert exc_info.value.response.status_code == 400
        assert exc_info.value.response.json()["detail"] == "Index not found"

    def test_create_binding_with_nonexistent_transformer(
        self, lx_client, celery_app, celery_worker
    ):
        with pytest.raises(LexyAPIError) as exc_info:
            lx_client.create_binding(
                collection_name="default",
                index_id="default_text_embeddings",
                transformer_id="nonexistent_transformer",
                description="Test Binding with Nonexistent Transformer",
            )
        assert isinstance(exc_info.value, LexyAPIError)
        assert (
            exc_info.value.response_data["status_code"] == 400
        ), exc_info.value.response_data
        assert exc_info.value.response.status_code == 400
        assert exc_info.value.response.json()["detail"] == "Transformer not found"

    def test_remove_filter_from_binding(self, lx_client, celery_app, celery_worker):
        # create filter
        my_filter = FilterBuilder()
        my_filter.include("meta.size", "less_than", 30000)
        my_filter.exclude("meta.type", "in", ["image", "video"])

        # create binding with filter
        binding = lx_client.create_binding(
            collection_name="default",
            index_id="default_text_embeddings",
            transformer_id="text.embeddings.minilm",
            description="Test Binding with Filter",
            filters=my_filter,
        )
        assert binding.binding_id is not None
        assert binding.description == "Test Binding with Filter"
        assert binding.filter == my_filter.to_dict()

        # update binding to remove filter
        updated_binding = lx_client.update_binding(
            binding_id=binding.binding_id, filters={}
        )
        assert updated_binding.binding_id == binding.binding_id
        assert updated_binding.filter is None

        # delete binding
        response = lx_client.delete_binding(binding_id=binding.binding_id)
        assert response == {"msg": "Binding deleted", "binding_id": binding.binding_id}


class TestBindingModel:
    def test_create_binding(self):
        binding = BindingCreate(
            collection_name="default",
            index_id="default_text_embeddings",
            transformer_id="text.embeddings.minilm",
        )
        assert binding.collection_name == "default"
        assert binding.index_id == "default_text_embeddings"
        assert binding.transformer_id == "text.embeddings.minilm"

    def test_create_binding_with_filter_obj(self):
        my_filter = FilterBuilder().include("meta.size", "less_than", 30000)
        binding = BindingCreate(
            collection_name="default",
            index_id="default_text_embeddings",
            transformer_id="text.embeddings.minilm",
            filter=my_filter,
        )
        assert binding.collection_name == "default"
        assert binding.index_id == "default_text_embeddings"
        assert binding.transformer_id == "text.embeddings.minilm"
        assert binding.filter == my_filter.to_dict()

    def test_create_binding_with_filter_as_dict(self):
        filter_dict = {
            "conditions": [
                {
                    "field": "meta.size",
                    "operation": "less_than",
                    "value": 30000,
                    "negate": False,
                }
            ],
            "combination": "AND",
        }
        binding = BindingCreate(
            collection_name="default",
            index_id="default_text_embeddings",
            transformer_id="text.embeddings.minilm",
            filter=filter_dict,
        )
        assert binding.collection_name == "default"
        assert binding.index_id == "default_text_embeddings"
        assert binding.transformer_id == "text.embeddings.minilm"
        assert binding.filter == filter_dict

    def test_create_binding_with_invalid_identifiers(self):
        with pytest.raises(ValueError):
            # collection identifiers missing
            BindingCreate(
                collection_id=None,
                collection_name=None,
                transformer_id="tid",
                index_id="iid",
                description="Binding with no valid collection identifier",
            )
        with pytest.raises(ValueError):
            # transformer identifiers missing
            BindingCreate(
                collection_id="cid",
                transformer_id=None,
                index_id="iid",
                description="Binding with no valid transformer identifier",
            )
        with pytest.raises(ValueError):
            # index identifiers missing
            BindingCreate(
                collection_id="cid",
                transformer_id="tid",
                description="Binding with no valid index identifier",
            )

    def test_update_binding(self):
        binding_update = BindingUpdate(description="Updated description", status="off")
        assert binding_update.description == "Updated description"
        assert binding_update.filter is None
        assert binding_update.execution_params is None
        assert binding_update.transformer_params is None
        assert binding_update.status == "off"

    def test_update_binding_with_filter_obj(self):
        my_filter = FilterBuilder().include("meta.size", "less_than", 30000)
        binding_update = BindingUpdate(
            description="Updated description", filter=my_filter
        )
        assert binding_update.description == "Updated description"
        assert binding_update.filter == my_filter.to_dict()
        assert binding_update.execution_params is None
        assert binding_update.transformer_params is None
        assert binding_update.status is None

    def test_update_binding_with_filter_as_dict(self):
        filter_dict = {
            "conditions": [
                {
                    "field": "meta.size",
                    "operation": "less_than",
                    "value": 30000,
                    "negate": False,
                }
            ],
            "combination": "AND",
        }
        binding_update = BindingUpdate(
            description="Updated description", filter=filter_dict
        )
        assert binding_update.description == "Updated description"
        assert binding_update.filter == filter_dict
        assert binding_update.execution_params is None
        assert binding_update.transformer_params is None
        assert binding_update.status is None
