import asyncio
import pytest
from sqlmodel import select

from lexy.models.collection import Collection
from lexy.models.document import Document, DocumentCreate, DocumentUpdate


class TestDocument:

    def test_hello(self):
        assert True

    @pytest.mark.asyncio
    async def test_create_document(self, async_session):
        result = await async_session.exec(
            select(Collection).where(Collection.collection_name == "default")
        )
        default_collection = result.first()
        document = Document(content="Test Content", collection_id=default_collection.collection_id)

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
        result = await async_session.exec(
            select(Collection).where(Collection.collection_name == "default")
        )
        default_collection = result.first()
        doc = Document(content="a shiny new document", collection_id=default_collection.collection_id)
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
        result = await async_session.exec(
            select(Collection).where(Collection.collection_name == "code")
        )
        code_collection = result.first()
        doc1 = Document(content="import this", collection_id=code_collection.collection_id)
        doc2 = Document(content="export that", collection_id=code_collection.collection_id)
        async_session.add(doc1)
        async_session.add(doc2)
        await async_session.commit()

        response = await async_client.get(
            "/api/documents", params={"collection_name": "code"}
        )
        assert response.status_code == 200, response.text

        data = response.json()
        assert len(data) == 2

        assert data[0]["content"] == "import this"
        assert data[0]["collection_id"] == code_collection.collection_id
        assert data[0]["document_id"] == str(doc1.document_id)
        assert data[0]["created_at"] == doc1.created_at.isoformat().replace("+00:00", "Z")
        assert data[0]["updated_at"] == doc1.updated_at.isoformat().replace("+00:00", "Z")

        assert data[1]["content"] == "export that"
        assert data[1]["collection_id"] == code_collection.collection_id
        assert data[1]["document_id"] == str(doc2.document_id)
        assert data[1]["created_at"] == doc2.created_at.isoformat().replace("+00:00", "Z")
        assert data[1]["updated_at"] == doc2.updated_at.isoformat().replace("+00:00", "Z")

    @pytest.mark.asyncio
    async def test_document_crud(self, async_session):
        # get default collection
        result = await async_session.exec(
            select(Collection).where(Collection.collection_name == "default")
        )
        default_collection = result.first()

        # create document
        document = DocumentCreate(content="Test Document CRUD")
        db_document = Document(**document.model_dump(), collection_id=default_collection.collection_id)
        async_session.add(db_document)
        await async_session.commit()
        await async_session.refresh(db_document)
        assert db_document.content == "Test Document CRUD"
        assert db_document.collection_id == default_collection.collection_id
        assert db_document.document_id is not None
        assert db_document.created_at is not None
        assert db_document.updated_at is not None
        doc_id = db_document.document_id

        # get document
        result = await async_session.exec(
            select(Document).where(Document.document_id == doc_id)
        )
        documents = result.all()
        assert len(documents) == 1
        assert documents[0].content == "Test Document CRUD"

        # update document
        document_update = DocumentUpdate(content="Test Document CRUD Updated")
        document_data = document_update.model_dump(exclude_unset=True)
        for key, value in document_data.items():
            setattr(db_document, key, value)
        async_session.add(db_document)
        await async_session.commit()
        await async_session.refresh(db_document)
        assert db_document.content == "Test Document CRUD Updated"
        assert db_document.created_at is not None
        assert db_document.updated_at > db_document.created_at
        result = await async_session.exec(
            select(Document).where(Document.document_id == doc_id)
        )
        documents = result.all()
        assert len(documents) == 1
        assert documents[0].content == "Test Document CRUD Updated"
        assert documents[0].created_at is not None
        assert documents[0].updated_at > documents[0].created_at

        # delete document
        result = await async_session.exec(
            select(Document).where(Document.document_id == doc_id)
        )
        doc_to_delete = result.first()
        assert doc_to_delete is not None
        await async_session.delete(doc_to_delete)
        await async_session.commit()

        result = await async_session.exec(
            select(Document).where(Document.document_id == doc_id)
        )
        doc_to_delete = result.first()
        assert doc_to_delete is None

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
