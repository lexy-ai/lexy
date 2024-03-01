from datetime import datetime

import asyncio
import pytest

from lexy_py.exceptions import LexyAPIError


class TestDocumentClient:

    def test_root(self, lx_client):
        response = lx_client.get("/")
        assert response.status_code == 200
        assert response.json() == {"Say": "Hello!"}

    def test_documents(self, lx_client):

        # create a test collection for test documents
        tmp_collection = lx_client.create_collection("tmp_collection", "Temp collection")
        assert tmp_collection.collection_id == "tmp_collection"

        # add documents to the test collection
        docs_added = lx_client.add_documents(docs=[
            {"content": "Test Document 1 Content"},
            {"content": "Test Document 2 Content", "meta": {"my_date": datetime.now()}}
        ], collection_id="tmp_collection")
        assert len(docs_added) == 2
        assert docs_added[0].content == "Test Document 1 Content"
        assert docs_added[1].content == "Test Document 2 Content"
        assert docs_added[0].document_id is not None
        assert docs_added[0].created_at is not None
        assert docs_added[0].image is None
        assert docs_added[0].collection_id == "tmp_collection"

        # get test document
        test_document = lx_client.get_document(docs_added[0].document_id)
        assert test_document.document_id == docs_added[0].document_id
        assert test_document.content == "Test Document 1 Content"

        # update test document
        doc_updated = lx_client.update_document(
            document_id=test_document.document_id,
            content="Test Document 1 Updated Content"
        )
        updated_document = lx_client.get_document(doc_updated.document_id)
        assert updated_document.document_id == test_document.document_id
        assert updated_document.content == "Test Document 1 Updated Content"
        assert updated_document.updated_at > updated_document.created_at

        # delete test document
        response = lx_client.delete_document(document_id=updated_document.document_id)
        assert response.get("msg") == "Document deleted"
        assert response.get("document_id") == updated_document.document_id

        # delete remaining test documents
        response = lx_client.delete_document(document_id=docs_added[1].document_id)
        assert response.get("msg") == "Document deleted"
        assert response.get("document_id") == docs_added[1].document_id

        # verify that there are no documents in the test collection
        documents = lx_client.list_documents(collection_id="tmp_collection")
        assert len(documents) == 0

        # delete test collection
        response = lx_client.delete_collection("tmp_collection")
        assert response.get("msg") == "Collection deleted"

    def test_duplicate_documents(self, lx_client):
        # create a test collection for testing duplicate documents
        tmp_collection = lx_client.create_collection("tmp_collection", "Temp collection")
        assert tmp_collection.collection_id == "tmp_collection"

        # add documents to the test collection
        docs_added = lx_client.add_documents(docs=[
            {"content": "What's up doc?"}
        ], collection_id="tmp_collection")
        assert len(docs_added) == 1
        doc_added = docs_added[0]
        assert doc_added.document_id is not None

        # add duplicate document
        with pytest.raises(LexyAPIError) as exc_info:
            lx_client.add_documents([
                doc_added
            ])
        assert isinstance(exc_info.value, LexyAPIError)
        assert exc_info.value.response.status_code == 400
        assert (exc_info.value.response.json()['detail']['msg'] ==
                f'A document with this ID already exists: {doc_added.document_id}.')
        assert exc_info.value.response.json()['detail']['document_id'] == doc_added.document_id

        # delete test documents
        response = lx_client.document.bulk_delete_documents(collection_id="tmp_collection")
        assert response.get("msg") == "Documents deleted"
        assert response.get("deleted_count") == 1

        # delete test collection
        response = lx_client.collection.delete_collection("tmp_collection")
        assert response.get("msg") == "Collection deleted"

    def test_add_documents_in_batches(self, lx_client):
        # create a test collection for testing adding documents in batches
        tmp_collection = lx_client.create_collection("tmp_collection", "Temp collection")
        assert tmp_collection.collection_id == "tmp_collection"

        # add documents to the test collection
        docs_added = lx_client.add_documents(
            docs=[
                {"content": "Test Document 1 Content"},
                {"content": "Test Document 2 Content"},
                {"content": "Test Document 3 Content"},
            ],
            collection_id="tmp_collection",
            batch_size=2)
        assert len(docs_added) == 3
        assert docs_added[-1].document_id is not None
        assert docs_added[-1].content == "Test Document 3 Content"

        # delete test documents
        response = lx_client.document.bulk_delete_documents(collection_id="tmp_collection")
        assert response.get("msg") == "Documents deleted"
        assert response.get("deleted_count") == 3

        # delete test collection
        response = lx_client.delete_collection("tmp_collection")
        assert response.get("msg") == "Collection deleted"
        assert response.get("collection_id") == "tmp_collection"

    @pytest.mark.asyncio
    async def test_add_documents(self, lx_client, celery_app, celery_worker):
        doc_added = lx_client.add_documents([
            {"content": "hello from lexy_py!"}
        ])
        print(f"{doc_added = }")
        assert len(doc_added) == 1
        assert doc_added[0].content == "hello from lexy_py!"
        assert doc_added[0].document_id is not None
        assert doc_added[0].created_at is not None
        assert doc_added[0].updated_at is not None
        assert doc_added[0].collection_id == "default"
        assert doc_added[0].image is None

        # wait for the celery worker to finish the task
        await asyncio.sleep(1)

        index_records = lx_client.index.list_index_records(
            index_id="default_text_embeddings",
            document_id=doc_added[0].document_id
        )
        assert len(index_records) == 1

    @pytest.mark.asyncio
    async def test_aadd_documents(self, lx_async_client, celery_app, celery_worker):
        doc_added = await lx_async_client.document.aadd_documents([
            {"content": "an async hello from lexy_py!"}
        ])
        print(f"{doc_added = }")
        assert len(doc_added) == 1
        assert doc_added[0].content == "an async hello from lexy_py!"
        assert doc_added[0].document_id is not None
        assert doc_added[0].created_at is not None
        assert doc_added[0].updated_at is not None
        assert doc_added[0].collection_id == "default"
        # FIXME: Uncomment the following line after fixing the simultaneous clients issue.
        #    The issue is caused by the following line when trying to access the image property:
        #      r = self.client.get(f"/documents/{document_id}/urls", params={"expiration": expiration})
        #    Need to figure out how to substitute get_document_urls with aget_document_urls.
        #    (Should also figure out why a simple text document is producing an object url)
        # assert doc_added[0].image is None

        # wait for the celery worker to finish the task
        await asyncio.sleep(1)

        index_records = await lx_async_client.index.alist_index_records(
            index_id="default_text_embeddings",
            document_id=doc_added[0].document_id
        )
        assert len(index_records) == 1

    def test_list_documents(self, lx_client):
        documents = lx_client.document.list_documents(collection_id='default')
        assert len(documents) > 0

    @pytest.mark.asyncio
    async def test_alist_documents(self, lx_async_client):
        documents = await lx_async_client.document.alist_documents(collection_id='default')
        assert len(documents) > 0
