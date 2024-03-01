import pytest

import lexy_py.document.models


class TestIndexClient:

    def test_root(self, lx_client):
        response = lx_client.get("/")
        assert response.status_code == 200
        assert response.json() == {"Say": "Hello!"}

    def test_indexes(self):
        # TODO: implement this after setting up mock for testing (do not run against live server)
        # # get all indexes
        # indexes = lexy.index.list_indexes()
        # assert len(indexes) > 0
        #
        # # create test index
        # test_index = lexy.index.add_index("test_index", "Test Index")
        # assert test_index.index_id == "test_index"
        # assert test_index.description == "Test Index"
        #
        # # get test index
        # test_index = lexy.index.get_index("test_index")
        # assert test_index.index_id == "test_index"
        # assert test_index.description == "Test Index"
        #
        # # update test index
        # test_index = lexy.index.update_index("test_index", "Test Index Updated")
        # assert test_index.index_id == "test_index"
        # assert test_index.description == "Test Index Updated"
        # assert test_index.updated_at > test_index.created_at
        #
        # # delete test index
        # response = lexy.index.delete_index("test_index")
        # assert response == {"msg": "Index deleted"}
        pass

    def test_list_indexes(self, lx_client):
        indexes = lx_client.list_indexes()
        assert len(indexes) > 0

    @pytest.mark.asyncio
    async def test_alist_indexes(self, lx_async_client):
        indexes = await lx_async_client.index.alist_indexes()
        assert len(indexes) > 0

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
