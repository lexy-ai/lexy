from datetime import datetime

import pytest

from lexy_py.client import LexyClient


lexy = LexyClient()


class TestDocumentClient:

    def test_root(self):
        response = lexy.get("/")
        assert response.status_code == 200
        assert response.json() == {"Say": "Hello!"}

    def test_documents(self):
        # get all documents
        documents = lexy.document.list_documents(collection_id='code')
        assert len(documents) > 0

        # create a test collection for test documents
        tmp_collection = lexy.collection.add_collection("tmp_collection", "Temp collection")
        assert tmp_collection.collection_id == "tmp_collection"

        # add documents to the test collection
        docs_added = lexy.document.add_documents(docs=[
            {"content": "Test Document 1 Content"},
            {"content": "Test Document 2 Content", "meta": {"my_date": datetime.now()}}
        ], collection_id="tmp_collection")
        assert len(docs_added) == 2
        assert docs_added[0].content == "Test Document 1 Content"
        assert docs_added[1].content == "Test Document 2 Content"
        assert docs_added[0].document_id is not None
        assert docs_added[0].created_at is not None
        assert docs_added[0].collection_id == "tmp_collection"

        # get test document
        test_document = lexy.document.get_document(docs_added[0].document_id)
        assert test_document.document_id == docs_added[0].document_id
        assert test_document.content == "Test Document 1 Content"

        # update test document
        doc_updated = lexy.document.update_document(
            document_id=test_document.document_id,
            content="Test Document 1 Updated Content"
        )
        updated_document = lexy.document.get_document(doc_updated.document_id)
        assert updated_document.document_id == test_document.document_id
        assert updated_document.content == "Test Document 1 Updated Content"
        assert updated_document.updated_at > updated_document.created_at

        # delete test document
        response = lexy.document.delete_document(document_id=updated_document.document_id)
        assert response == {"Say": "Document deleted!"}

        # delete remaining test documents
        response = lexy.document.delete_document(document_id=docs_added[1].document_id)
        assert response == {"Say": "Document deleted!"}

        # verify that there are no documents in the test collection
        documents = lexy.document.list_documents(collection_id="tmp_collection")
        assert len(documents) == 0

        # delete test collection
        response = lexy.collection.delete_collection("tmp_collection")
        assert response.get("Say") == "Collection deleted!"

    def test_list_documents(self):
        documents = lexy.document.list_documents(collection_id='code')
        assert len(documents) > 0

    @pytest.mark.asyncio
    async def test_alist_documents(self):
        documents = await lexy.document.alist_documents(collection_id='code')
        assert len(documents) > 0
