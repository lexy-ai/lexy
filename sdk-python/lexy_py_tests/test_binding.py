import pytest

from lexy_py.client import LexyClient
from lexy_py.collection.models import Collection
from lexy_py.index.models import Index
from lexy_py.transformer.models import Transformer


class TestBindingClient:

    def test_root(self, lx_client):
        response = lx_client.get("/")
        assert response.status_code == 200
        assert response.json() == {"Say": "Hello!"}

    def test_bindings(self):
        # TODO: implement this after setting up mock for testing (do not run against live server)
        pass

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
