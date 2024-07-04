import pytest
from sqlmodel import select

from lexy import crud
from lexy.models.binding import Binding, BindingCreate, BindingRead, BindingUpdate
from lexy.models.collection import Collection
from lexy.models.index import Index
from lexy.models.transformer import Transformer


class TestBinding:
    def test_hello(self):
        assert True

    @pytest.mark.asyncio
    async def test_get_bindings(self, async_session):
        result = await async_session.exec(select(Binding))
        bindings = result.all()
        assert len(bindings) > 0

        b = bindings[0]
        assert b.binding_id == 1
        assert b.description == "Default binding"

        # these should be present for BindingRead class only
        assert "collection" not in b.model_dump()
        assert "transformer" not in b.model_dump()
        assert "index" not in b.model_dump()

    def test_get_bindings_with_client(self, client):
        response = client.get(
            "/api/bindings",
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert len(data) > 0

        b = data[0]
        assert b["binding_id"] == 1
        assert b["description"] == "Default binding"

        # these should be present for BindingRead class only
        assert "collection" in b
        assert "transformer" in b
        assert "index" in b

        binding = BindingRead.model_validate(b)
        assert binding.binding_id == 1
        assert isinstance(binding.collection, Collection)
        assert binding.collection.collection_name == "default"
        assert isinstance(binding.index, Index)
        assert binding.index.index_id == "default_text_embeddings"
        assert isinstance(binding.transformer, Transformer)
        assert binding.transformer.transformer_id == "text.embeddings.minilm"

    @pytest.mark.asyncio
    async def test_get_bindings_with_async_client(self, async_client):
        response = await async_client.get(
            "/api/bindings",
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert len(data) > 0

        b = data[0]
        assert b["binding_id"] == 1
        assert b["description"] == "Default binding"

        # these should be present for BindingRead class only
        assert "collection" in b
        assert "transformer" in b
        assert "index" in b

        binding = BindingRead.model_validate(b)
        assert binding.binding_id == 1
        assert isinstance(binding.collection, Collection)
        assert binding.collection.collection_name == "default"
        assert isinstance(binding.index, Index)
        assert binding.index.index_id == "default_text_embeddings"
        assert isinstance(binding.transformer, Transformer)
        assert binding.transformer.transformer_id == "text.embeddings.minilm"

    @pytest.mark.asyncio
    async def test_create_and_delete_binding(self, async_session):
        b_dict = {
            "collection_name": "default",
            "transformer_id": "text.embeddings.minilm",
            "index_id": "default_text_embeddings",
            "description": "Test binding with filter",
            "execution_params": {},
            "transformer_params": {},
            "filter": {
                "conditions": [
                    {
                        "field": "meta.size",
                        "operation": "less_than",
                        "value": 30000.0,
                        "negate": False,
                    }
                ],
                "combination": "AND",
            },
        }
        b = BindingCreate.model_validate(b_dict)
        collection = await crud.get_collection_by_name(
            session=async_session, collection_name=b.collection_name
        )
        assert collection is not None
        assert collection.collection_id is not None
        assert collection.collection_name == "default"
        b.collection_id = collection.collection_id

        binding = Binding(**b.model_dump())
        async_session.add(binding)
        await async_session.commit()
        await async_session.refresh(binding)
        assert binding.binding_id is not None
        assert binding.description == "Test binding with filter"
        assert binding.created_at is not None
        assert binding.updated_at is not None
        assert binding.collection_id == collection.collection_id

        result = await async_session.exec(
            select(Binding).where(Binding.binding_id == binding.binding_id)
        )
        bindings = result.all()
        assert len(bindings) == 1
        assert bindings[0].binding_id == binding.binding_id
        assert bindings[0].description == "Test binding with filter"

        # delete binding
        await async_session.delete(bindings[0])
        await async_session.commit()

        result = await async_session.exec(
            select(Binding).where(Binding.binding_id == binding.binding_id)
        )
        bindings = result.all()
        assert len(bindings) == 0


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
        binding_update = BindingUpdate(
            description="Updated description",
            filter={
                "conditions": [
                    {
                        "field": "meta.size",
                        "operation": "less_than",
                        "value": 30000,
                        "negate": False,
                    }
                ],
                "combination": "AND",
            },
        )
        assert binding_update.description == "Updated description"
        assert binding_update.filter is not None
        assert binding_update.execution_params is None
        assert binding_update.transformer_params is None
        assert binding_update.status is None
