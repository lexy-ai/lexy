import pytest

from lexy_py.client import LexyClient
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
        assert binding.collection.collection_id == "default"
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
        assert binding.collection.collection_id == "default"
        assert isinstance(binding.collection.client, LexyClient)

        assert isinstance(binding.index, Index)
        assert binding.index.index_id == "default_text_embeddings"
        assert isinstance(binding.index.client, LexyClient)

        assert isinstance(binding.transformer, Transformer)
        assert binding.transformer.transformer_id == "text.embeddings.minilm"
        assert isinstance(binding.transformer.client, LexyClient)

    def test_create_binding(self, lx_client, celery_app, celery_worker):
        binding = lx_client.create_binding(
            collection_id="default",
            index_id="default_text_embeddings",
            transformer_id="text.embeddings.minilm",
            description="Test Binding"

        )
        assert binding.binding_id is not None
        assert binding.collection.collection_id == "default"
        assert binding.index.index_id == "default_text_embeddings"
        assert binding.transformer.transformer_id == "text.embeddings.minilm"
        assert binding.description == "Test Binding"
        assert binding.status == "on"
        assert "lexy_index_fields" in binding.transformer_params
        assert set(binding.index.index_fields.keys()) == set(binding.transformer_params["lexy_index_fields"])

        # delete test binding
        response = lx_client.delete_binding(binding_id=binding.binding_id)
        assert response == {
            "msg": "Binding deleted",
            "binding_id": binding.binding_id
        }

    def test_update_binding_with_filter(self, lx_client, celery_app, celery_worker):
        binding = lx_client.create_binding(
            collection_id="default",
            index_id="default_text_embeddings",
            transformer_id="text.embeddings.minilm",
            description="Test Binding"
        )
        assert binding.binding_id is not None
        assert binding.collection.collection_id == "default"
        assert binding.index.index_id == "default_text_embeddings"
        assert binding.transformer.transformer_id == "text.embeddings.minilm"
        assert binding.description == "Test Binding"
        assert binding.status == "on"
        assert "lexy_index_fields" in binding.transformer_params
        assert set(binding.index.index_fields.keys()) == set(binding.transformer_params["lexy_index_fields"])
        assert binding.filter is None

        # create filter
        my_filter = (FilterBuilder().include("meta.size", "less_than", 30000)
                                    .exclude("meta.type", "in", ["image", "video"]))

        # update binding description and filter
        binding = lx_client.update_binding(
            binding_id=binding.binding_id,
            description="Test Binding with Filter",
            filters=my_filter
        )
        assert binding.binding_id is not None
        assert binding.description == "Test Binding with Filter"
        assert binding.filter is not None
        assert binding.filter == my_filter.to_dict()

        # delete test binding
        response = lx_client.delete_binding(binding_id=binding.binding_id)
        assert response == {
            "msg": "Binding deleted",
            "binding_id": binding.binding_id
        }

    def test_create_binding_with_invalid_filter(self, lx_client, celery_app, celery_worker):
        # create filter with invalid conditions
        my_filter = (FilterBuilder().include("meta.size", "less_than", "hello"))

        with pytest.raises(LexyAPIError) as exc_info:
            lx_client.create_binding(
                collection_id="default",
                index_id="default_text_embeddings",
                transformer_id="text.embeddings.minilm",
                description="Test Binding with Invalid Filter",
                filters=my_filter
            )
        assert isinstance(exc_info.value, LexyAPIError)
        assert exc_info.value.response_data["status_code"] == 422, exc_info.value.response_data
        assert exc_info.value.response.status_code == 422
        assert len(exc_info.value.response.json()["detail"]) == 1
        error = exc_info.value.response.json()["detail"][0]
        assert error["type"] == "value_error"
        assert error["loc"] == ["body", "filter", "conditions", 0, "value"]
        assert error["msg"] == "Value error, Value must be a number for operation 'less_than'"
        assert error["input"] == "hello"
