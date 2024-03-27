import pytest
from sqlmodel import select

from lexy.models.index import Index, IndexCreate


class TestIndex:

    def test_hello(self):
        assert True

    @pytest.mark.asyncio
    async def test_get_indexes(self, async_session):
        result = await async_session.exec(select(Index))
        indexes = result.all()
        assert len(indexes) == 1
        index_ids = [index.index_id for index in indexes]
        assert "default_text_embeddings" in index_ids

    def test_get_indexes_with_client(self, client):
        response = client.get(
            "/api/indexes",
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert len(data) == 1
        index_ids = [index['index_id'] for index in data]
        assert "default_text_embeddings" in index_ids

    @pytest.mark.asyncio
    async def test_get_indexes_with_async_client(self, async_client):
        response = await async_client.get(
            "/api/indexes",
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert len(data) == 1
        index_ids = [index['index_id'] for index in data]
        assert "default_text_embeddings" in index_ids

    @pytest.mark.asyncio
    async def test_get_index(self, async_session):
        result = await async_session.exec(
            select(Index).where(Index.index_id == "default_text_embeddings")
        )
        index = result.first()
        assert index.index_id == "default_text_embeddings"
        assert index.description == "Text embeddings for default collection"
        assert set(index.index_fields.keys()) == {"text", "embedding"}

    @pytest.mark.asyncio
    async def test_create_index_row_only(self, async_session):
        # define index fields
        test_index_fields = {
            "text": {"type": "text"},
            "embedding": {"type": "embedding", "extras": {"dims": 384, "model": "text.embeddings.minilm"}},
            "meta": {"type": "object"},
        }
        index = IndexCreate(index_id="test_index", description="Test Index", index_fields=test_index_fields)

        db_index = Index.model_validate(index)
        async_session.add(db_index)
        await async_session.commit()
        await async_session.refresh(db_index)
        assert db_index.index_id == "test_index"
        assert db_index.description == "Test Index"

        result = await async_session.exec(
            select(Index).where(Index.index_id == "test_index")
        )
        indexes = result.all()
        assert len(indexes) == 1
        test_index = indexes[0]
        assert test_index.index_id == "test_index"
        assert test_index.description == "Test Index"
        assert set(test_index.index_fields.keys()) == {"text", "embedding", "meta"}

    @pytest.mark.asyncio
    async def test_delete_index_row_only(self, async_session):
        result = await async_session.exec(select(Index).where(Index.index_id == "test_index"))
        index = result.first()
        assert index is not None

        await async_session.delete(index)
        await async_session.commit()

        result = await async_session.exec(select(Index).where(Index.index_id == "test_index"))
        index = result.first()
        assert index is None


class TestIndexManager:
    # TODO: create fixture for IndexManager and run all relevant tests
    #   - test creating index model
    #   - test creating index table
    #   - test saving index record(s)
    #   - test getting index record(s)
    #   - test updating index record(s)
    #   - test deleting index record(s)
    #   - test dropping index table
    pass


class TestIndexModel:

    def test_create_index(self):
        index = IndexCreate(index_id="test_index")
        assert index.index_id == "test_index"
        index = IndexCreate(index_id="_te5t")
        assert index.index_id == "_te5t"
        index = IndexCreate(index_id="_myindex" * 7)
        assert index.index_id == "_myindex" * 7

    def test_create_index_with_invalid_id(self):
        with pytest.raises(ValueError):
            IndexCreate(index_id="", description="Test Index")  # blank
        with pytest.raises(ValueError):
            IndexCreate(index_id="test index", description="Test Index")  # space
        with pytest.raises(ValueError):
            IndexCreate(index_id="test-index", description="Test Index")  # hyphen
        with pytest.raises(ValueError):
            IndexCreate(index_id="Test", description="Test Index")  # uppercase
        with pytest.raises(ValueError):
            IndexCreate(index_id="1abc", description="Test Index")  # starts with number
        with pytest.raises(ValueError):
            IndexCreate(index_id="_myindex" * 8, description="Test Index")  # too long
