import pytest

import lexy_py.document.models
from lexy_py.client import LexyClient


lexy = LexyClient()


class TestIndexClient:

    def test_root(self):
        response = lexy.get("/")
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
        # assert response == {"Say": "Index deleted!"}
        pass

    def test_list_indexes(self):
        indexes = lexy.index.list_indexes()
        assert len(indexes) > 0

    @pytest.mark.asyncio
    async def test_alist_indexes(self):
        indexes = await lexy.index.alist_indexes()
        assert len(indexes) > 0

    def test_query_index(self):
        results = lexy.index.query_index(
            query_text="Test Query", index_id="default_text_embeddings", k=5
        )
        assert len(results) >= 0
        results = lexy.index.query_index(
            query_text="Test Query", index_id="default_text_embeddings", k=5, return_document=True
        )
        assert len(results) >= 0
        if len(results) > 0:
            result_doc = results[0].get('document')
            assert isinstance(result_doc, lexy_py.document.models.Document)
            assert result_doc.document_id == results[0].get('document_id')

    @pytest.mark.asyncio
    async def test_aquery_index(self):
        results = await lexy.index.aquery_index(
            query_text="Test Query", index_id="default_text_embeddings", k=5
        )
        assert len(results) >= 0
        results = await lexy.index.aquery_index(
            query_text="Test Query", index_id="default_text_embeddings", k=5, return_document=True
        )
        assert len(results) >= 0
        if len(results) > 0:
            result_doc = results[0].get('document')
            assert isinstance(result_doc, lexy_py.document.models.Document)
            assert result_doc.document_id == results[0].get('document_id')

    def test_list_index_records(self):
        records = lexy.index.list_index_records(index_id="default_text_embeddings")
        assert len(records) >= 0

    @pytest.mark.asyncio
    async def test_alist_index_records(self):
        records = await lexy.index.alist_index_records(index_id="default_text_embeddings")
        assert len(records) >= 0
