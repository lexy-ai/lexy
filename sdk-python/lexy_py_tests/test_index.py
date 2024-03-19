import pytest

import lexy_py.document.models
from lexy_py.exceptions import LexyAPIError, NotFoundError


class TestIndexClient:

    def test_root(self, lx_client):
        response = lx_client.get("/")
        assert response.status_code == 200
        assert response.json() == {"Say": "Hello!"}

    def test_create_index(self, lx_client, celery_app, celery_worker):
        # define index fields
        test_index_fields = {
            "text": {"type": "text"},
            "embedding": {"type": "embedding", "extras": {"dims": 384, "model": "text.embeddings.minilm"}},
            "meta": {"type": "object"},
        }
        # create index
        test_index = lx_client.create_index(
            index_id="test_index",
            description="Test Index",
            index_fields=test_index_fields
        )
        assert test_index.index_id == "test_index"
        assert test_index.description == "Test Index"
        assert set(test_index.index_fields.keys()) == {"text", "embedding", "meta"}

    def test_get_index(self, lx_client):
        test_index = lx_client.get_index("test_index")
        assert test_index.index_id == "test_index"
        assert test_index.description == "Test Index"
        assert set(test_index.index_fields.keys()) == {"text", "embedding", "meta"}

    @pytest.mark.asyncio
    async def test_aget_index(self, lx_async_client):
        test_index = await lx_async_client.index.aget_index("test_index")
        assert test_index.index_id == "test_index"
        assert test_index.description == "Test Index"
        assert set(test_index.index_fields.keys()) == {"text", "embedding", "meta"}

    def test_update_index(self, lx_client):
        test_index = lx_client.update_index("test_index", description="Test Index Updated")
        assert test_index.index_id == "test_index"
        assert test_index.description == "Test Index Updated"
        assert test_index.updated_at > test_index.created_at

    @pytest.mark.asyncio
    async def test_aupdate_index(self, lx_async_client):
        test_index = await lx_async_client.index.aupdate_index("test_index", description="Test Index Async Update")
        assert test_index.index_id == "test_index"
        assert test_index.description == "Test Index Async Update"
        assert test_index.updated_at > test_index.created_at

    def test_delete_index(self, lx_client):
        response = lx_client.delete_index("test_index", drop_table=True)
        assert response == {
            "msg": "Index deleted",
            "index_id": "test_index",
            "index_table_name": "zzidx__test_index",
            "table_dropped": True
        }, response

    def test_list_indexes(self, lx_client):
        indexes = lx_client.list_indexes()
        assert len(indexes) > 0
        index_ids = [index.index_id for index in indexes]
        assert "default_text_embeddings" in index_ids
        assert "test_index" not in index_ids

    @pytest.mark.asyncio
    async def test_alist_indexes(self, lx_async_client):
        indexes = await lx_async_client.index.alist_indexes()
        assert len(indexes) > 0
        index_ids = [index.index_id for index in indexes]
        assert "default_text_embeddings" in index_ids
        assert "test_index" not in index_ids

    def test_query_index(self, lx_client, celery_app, celery_worker):
        results = lx_client.query_index(
            query_text="Test Query", index_id="default_text_embeddings", k=5
        )
        assert len(results) >= 0
        results = lx_client.query_index(
            query_text="Test Query", index_id="default_text_embeddings", k=5, return_document=True
        )
        assert len(results) >= 0
        if len(results) > 0:
            result_doc = results[0].get('document')
            assert isinstance(result_doc, lexy_py.document.models.Document)
            assert result_doc.document_id == results[0].get('document_id')

    @pytest.mark.asyncio
    async def test_aquery_index(self, lx_async_client, celery_app, celery_worker):
        results = await lx_async_client.index.aquery_index(
            query_text="Test Query", index_id="default_text_embeddings", k=5
        )
        assert len(results) >= 0
        results = await lx_async_client.index.aquery_index(
            query_text="Test Query", index_id="default_text_embeddings", k=5, return_document=True
        )
        assert len(results) >= 0
        if len(results) > 0:
            result_doc = results[0].get('document')
            assert isinstance(result_doc, lexy_py.document.models.Document)
            assert result_doc.document_id == results[0].get('document_id')

    def test_list_index_records(self, lx_client):
        records = lx_client.index.list_index_records(index_id="default_text_embeddings")
        assert len(records) >= 0

    @pytest.mark.asyncio
    async def test_alist_index_records(self, lx_async_client):
        records = await lx_async_client.index.alist_index_records(index_id="default_text_embeddings")
        assert len(records) >= 0

    def test_query_nonexistent_index_field(self, lx_client):
        with pytest.raises(NotFoundError) as exc_info:
            lx_client.index.query_index("this should fail!", query_field="not_a_real_field")
        assert exc_info.value.response_data["status_code"] == 404, exc_info.value.response_data
        assert exc_info.value.response.status_code == 404
        assert exc_info.value.response.text == ('{"detail":"Field \'not_a_real_field\' not found in index '
                                                '\'default_text_embeddings\'"}')

    def test_query_return_nonexistent_index_field(self, lx_client, celery_app, celery_worker):
        with pytest.raises(LexyAPIError) as exc_info:
            lx_client.index.query_index("this should also fail!", return_fields=["not_an_index_field"])
        assert exc_info.value.response_data["status_code"] == 400, exc_info.value.response_data
        assert exc_info.value.response.status_code == 400
        assert exc_info.value.response.text == ('{"detail":"Field \'not_an_index_field\' not found in index '
                                                '\'default_text_embeddings\'"}')

    def test_query_return_nonexistent_document_field(self, lx_client, celery_app, celery_worker):
        with pytest.raises(LexyAPIError) as exc_info:
            lx_client.index.query_index("this one too!", return_fields=["document.not_a_document_field"])
        assert exc_info.value.response_data["status_code"] == 400, exc_info.value.response_data
        assert exc_info.value.response.status_code == 400
        assert exc_info.value.response.text == '{"detail":"Field \'not_a_document_field\' not found in document"}'
