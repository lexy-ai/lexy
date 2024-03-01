import pytest


class TestTransformerClient:

    def test_root(self, lx_client):
        response = lx_client.get("/")
        assert response.status_code == 200
        assert response.json() == {"Say": "Hello!"}

    def test_transformers(self, lx_client):
        # get all transformers
        transformers = lx_client.list_transformers()
        assert len(transformers) > 0

        # create test transformer
        test_transformer = lx_client.create_transformer("test_transformer", "test.tester", "Test Transformer")
        assert test_transformer.transformer_id == "test_transformer"
        assert test_transformer.path == "test.tester"
        assert test_transformer.description == "Test Transformer"

        # get test transformer
        test_transformer = lx_client.get_transformer("test_transformer")
        assert test_transformer.transformer_id == "test_transformer"
        assert test_transformer.path == "test.tester"
        assert test_transformer.description == "Test Transformer"

        # update test transformer
        test_transformer = lx_client.update_transformer("test_transformer", path="test.tester2")
        assert test_transformer.transformer_id == "test_transformer"
        assert test_transformer.path == "test.tester2"
        assert test_transformer.description == "Test Transformer"

        # delete test transformer
        response = lx_client.delete_transformer("test_transformer")
        assert response.get("msg") == "Transformer deleted"
        assert response.get("transformer_id") == "test_transformer"

    def test_list_transformers(self, lx_client):
        transformers = lx_client.transformer.list_transformers()
        assert len(transformers) > 0

    @pytest.mark.asyncio
    async def test_alist_transformers(self, lx_async_client):
        transformers = await lx_async_client.transformer.alist_transformers()
        assert len(transformers) > 0

    def test_transform_document(self, lx_client, celery_app, celery_worker):
        transformer = lx_client.transformer.get_transformer("text.embeddings.minilm")
        response = transformer.transform_document({"content": "Hello, world!"})
        assert 'task_id' in response
        assert isinstance(response["result"], list)
        assert all(isinstance(elem, float) for elem in response["result"])
