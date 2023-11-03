import pytest

from sqlmodel import select

from lexy.models.document import DocumentCreate, Document
# from lexy.main import app


class TestDocument:

    def test_hello(self):
        assert True

    def test_root(self, client):
        response = client.get("/api")
        assert response.status_code == 200
        assert response.json() == {"Say": "Hello!"}

    @pytest.mark.asyncio
    async def test_aroot(self, client):
        response = client.get("/api")
        assert response.status_code == 200
        assert response.json() == {"Say": "Hello!"}

    @pytest.mark.asyncio
    async def test_create_document(self, async_session):
        document = DocumentCreate(
            content="Test Content"
        )
        document = Document(**document.dict())
        async_session.add(document)
        await async_session.commit()
        await async_session.refresh(document)
        assert document.content == "Test Content"
        assert document.document_id is not None
        assert document.created_at is not None
        assert document.updated_at is not None

    @pytest.mark.asyncio
    async def test_get_ping(self, async_client):
        response = await async_client.get(
            "/api/ping",
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data == {"ping": "pong!"}

    @pytest.mark.asyncio
    async def test_get_documents(self, async_client):
        response = await async_client.get(
            "/api/documents",
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert len(data) > 0

    # @pytest.mark.asyncio
    # def test_create_documents(self, client):
    #     response = client.post(
    #         "/api/documents/",
    #         data=b'[{"content": "hello there!"}]',
    #         headers={"Content-Type": "application/json", "Accept": "application/json"}
    #     )
    #     assert response.status_code == 201, response.text
    #     data = response.json()
    #     assert data == {"Say": "Documents added!"}
    #
    # @pytest.mark.asyncio
    # async def test_create_and_get_documents(self, async_client):
    #     response = await async_client.post(
    #         "/api/documents/",
    #         data=b'[{"content": "hello there!"}]',
    #         headers={"Content-Type": "application/json", "Accept": "application/json"},
    #     )
    #     assert response.status_code == 201, response.text
    #     data = response.json()
    #     assert data == {"Say": "Documents added!"}

    # @pytest.mark.asyncio
    # async def test_create_and_get_documents(self):
    #     async with AsyncClient(app=app, base_url='http://127.0.0.1:9900', follow_redirects=True) as async_client:
    #         response = await async_client.post(
    #             "/api/documents",
    #             json=[{"content": "hello there!"}],
    #         )
    #         assert response.status_code == 200, response.text
    #         data = response.json()
    #         assert data == {"Say": "Documents added!"}

    @pytest.mark.asyncio
    async def test_get_documents(self, async_session):
        result = await async_session.execute(select(Document))
        documents = result.scalars().all()
        assert len(documents) > 0
        assert documents[0].content == "Test Content"
        assert documents[0].document_id is not None
        assert documents[0].created_at is not None
        assert documents[0].updated_at is not None
