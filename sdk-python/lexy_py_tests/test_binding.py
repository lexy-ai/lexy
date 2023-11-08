import pytest

from lexy_py.client import LexyClient
from lexy_py.collection.models import Collection
from lexy_py.index.models import Index
from lexy_py.transformer.models import Transformer


lexy = LexyClient()


class TestBindingClient:

    def test_root(self):
        response = lexy.get("/")
        assert response.status_code == 200
        assert response.json() == {"Say": "Hello!"}

    def test_bindings(self):
        # TODO: implement this after setting up mock for testing (do not run against live server)
        pass

    def test_list_bindings(self):
        bindings = lexy.binding.list_bindings()
        assert len(bindings) > 0

    @pytest.mark.asyncio
    async def test_alist_bindings(self):
        bindings = await lexy.binding.alist_bindings()
        assert len(bindings) > 0

    def test_get_binding(self):
        binding = lexy.binding.get_binding(binding_id=1)
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
    async def test_aget_binding(self):
        binding = await lexy.binding.aget_binding(binding_id=1)
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
