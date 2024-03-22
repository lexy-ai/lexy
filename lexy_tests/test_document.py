import asyncio
import pytest
from sqlmodel import select

from lexy.models.document import Document


class TestDocument:

    def test_hello(self):
        assert True

    @pytest.mark.asyncio
    async def test_create_document(self, async_session):
        document = Document(content="Test Content")
        async_session.add(document)
        await async_session.commit()
        await async_session.refresh(document)
        assert document.content == "Test Content"
        assert document.document_id is not None
        assert document.created_at is not None
        assert document.updated_at is not None

        result = await async_session.exec(select(Document))
        documents = result.all()
        assert len(documents) == 1
        assert documents[0].content == "Test Content"

    @pytest.mark.asyncio
    async def test_get_documents_with_async_client(self, async_client):
        response = await async_client.get(
            "/api/documents",
        )
        assert response.status_code == 200, response.text

        data = response.json()
        assert len(data) == 1
        assert data[0]["content"] == "Test Content"

    @pytest.mark.asyncio
    async def test_add_document(self, async_session, async_client):
        doc = Document(content="a shiny new document")
        async_session.add(doc)
        await async_session.commit()

        response = await async_client.get(
            f"/api/documents/{doc.document_id}",
        )
        assert response.status_code == 200, response.text

        data = response.json()
        assert data["content"] == doc.content
        assert data["document_id"] == str(doc.document_id)
        assert data["created_at"] == doc.created_at.isoformat().replace("+00:00", "Z")
        assert data["updated_at"] == doc.updated_at.isoformat().replace("+00:00", "Z")

    @pytest.mark.asyncio
    async def test_add_documents(self, async_session, async_client):
        doc1 = Document(content="import this", collection_id='code')
        doc2 = Document(content="export that", collection_id='code')
        async_session.add(doc1)
        # TODO: remove the next line and use only a single commit
        #  Requires SQLModel to update the GUID class, or SQLAlchemy update to 2.0.29. See the issues below.
        #  - SQLAlchemy: https://github.com/sqlalchemy/sqlalchemy/issues/11160
        #  - SQLModel: https://github.com/tiangolo/sqlmodel/discussions/843
        await async_session.commit()
        async_session.add(doc2)
        await async_session.commit()

        response = await async_client.get(
            "/api/documents", params={"collection_id": "code"}
        )
        assert response.status_code == 200, response.text

        data = response.json()
        assert len(data) == 2

        assert data[0]["content"] == "import this"
        assert data[0]["collection_id"] == "code"
        assert data[0]["document_id"] == str(doc1.document_id)
        assert data[0]["created_at"] == doc1.created_at.isoformat().replace("+00:00", "Z")
        assert data[0]["updated_at"] == doc1.updated_at.isoformat().replace("+00:00", "Z")

        assert data[1]["content"] == "export that"
        assert data[1]["collection_id"] == "code"
        assert data[1]["document_id"] == str(doc2.document_id)
        assert data[1]["created_at"] == doc2.created_at.isoformat().replace("+00:00", "Z")
        assert data[1]["updated_at"] == doc2.updated_at.isoformat().replace("+00:00", "Z")

    @pytest.mark.asyncio
    async def test_add_documents_with_async_client(self, async_client, celery_app, celery_worker):
        response = await async_client.post(
            "/api/documents",
            json=[{"content": "hello there!"}],
        )
        assert response.status_code == 201, response.text

        data = response.json()
        assert len(data) == 1
        assert set(data[0].keys()) == {"document", "tasks"}
        assert data[0]["document"]["content"] == "hello there!"
        doc_id = data[0]["document"]["document_id"]

        # wait for the celery worker to finish the task
        await asyncio.sleep(1)

        # retrieve the index records for default_text_embeddings
        records_response = await async_client.get(
            "/api/indexes/default_text_embeddings/records",
        )
        assert records_response.status_code == 200, records_response.text
        records_data = records_response.json()
        assert len(records_data) == 1
        assert records_data[0]["document_id"] == doc_id
        index_record_id = records_data[0]["index_record_id"]

        # retrieve the index record by id
        index_record_response = await async_client.get(
            f"/api/indexes/default_text_embeddings/records/{index_record_id}",
        )
        assert index_record_response.status_code == 200, index_record_response.text
        index_record_data = index_record_response.json()
        assert index_record_data["document_id"] == doc_id
        assert index_record_data["index_record_id"] == index_record_id
