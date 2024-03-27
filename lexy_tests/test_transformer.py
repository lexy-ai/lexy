import pytest
from sqlmodel import select

from lexy.models.transformer import Transformer, TransformerCreate


class TestTransformer:

    def test_hello(self):
        assert True

    @pytest.mark.asyncio
    async def test_get_transformers(self, async_session):
        result = await async_session.exec(select(Transformer))
        transformers = result.all()
        assert len(transformers) > 1
        transformer_ids = [t.transformer_id for t in transformers]
        assert "text.embeddings.minilm" in transformer_ids

    def test_get_transformers_with_client(self, client):
        response = client.get(
            "/api/transformers",
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert len(data) > 1
        transformer_ids = [t['transformer_id'] for t in data]
        assert "text.embeddings.minilm" in transformer_ids

    @pytest.mark.asyncio
    async def test_get_transformers_with_async_client(self, async_client):
        response = await async_client.get(
            "/api/transformers",
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert len(data) > 1
        transformer_ids = [t['transformer_id'] for t in data]
        assert "text.embeddings.minilm" in transformer_ids

    @pytest.mark.asyncio
    async def test_create_transformer(self, async_session):
        transformer = TransformerCreate(
            transformer_id="test_transformer",
            path="test.tester",
            description="Test Transformer"
        )

        db_transformer = Transformer.model_validate(transformer)
        async_session.add(db_transformer)
        await async_session.commit()
        await async_session.refresh(db_transformer)
        assert db_transformer.transformer_id == "test_transformer"
        assert db_transformer.path == "test.tester"
        assert db_transformer.description == "Test Transformer"
        assert db_transformer.celery_task_name == "lexy.transformers.test_transformer"

        result = await async_session.exec(
            select(Transformer).where(Transformer.transformer_id == "test_transformer")
        )
        transformers = result.all()
        assert len(transformers) == 1
        assert transformers[0].transformer_id == "test_transformer"
        assert transformers[0].path == "test.tester"
        assert transformers[0].description == "Test Transformer"

    @pytest.mark.asyncio
    async def test_delete_transformer(self, async_session):
        result = await async_session.exec(
            select(Transformer).where(Transformer.transformer_id == "test_transformer")
        )
        transformer = result.first()
        assert transformer is not None

        await async_session.delete(transformer)
        await async_session.commit()

        result = await async_session.exec(
            select(Transformer).where(Transformer.transformer_id == "test_transformer")
        )
        transformer = result.first()
        assert transformer is None


class TestTransformerModel:

    def test_create_transformer(self):
        transformer = TransformerCreate(transformer_id="test_transformer")
        assert transformer.transformer_id == "test_transformer"
        transformer = TransformerCreate(transformer_id="test-transformer")
        assert transformer.transformer_id == "test-transformer"
        transformer = TransformerCreate(transformer_id="test.transformer")
        assert transformer.transformer_id == "test.transformer"

    def test_create_transformer_with_invalid_id(self):
        with pytest.raises(ValueError):
            TransformerCreate(transformer_id="", description="Test Transformer")  # blank
        with pytest.raises(ValueError):
            TransformerCreate(transformer_id="test transformer", description="Test Transformer")  # space
        with pytest.raises(ValueError):
            TransformerCreate(transformer_id="_test", description="Test Transformer")  # starts with underscore
        with pytest.raises(ValueError):
            TransformerCreate(transformer_id="1abc", description="Test Transformer")  # starts with number
        with pytest.raises(ValueError):
            TransformerCreate(transformer_id="transformer" * 30, description="Test Transformer")  # too long
