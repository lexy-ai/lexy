import pytest

from lexy_py.client import LexyClient


lexy = LexyClient()


class TestTransformerClient:

    def test_root(self):
        response = lexy.get("/")
        assert response.status_code == 200
        assert response.json() == {"Say": "Hello!"}

    def test_transformers(self):
        # get all transformers
        transformers = lexy.transformer.list_transformers()
        assert len(transformers) > 0

        # create test transformer
        test_transformer = lexy.transformer.add_transformer("test_transformer", "test.tester", "Test Transformer")
        assert test_transformer.transformer_id == "test_transformer"
        assert test_transformer.path == "test.tester"
        assert test_transformer.description == "Test Transformer"

        # get test transformer
        test_transformer = lexy.transformer.get_transformer("test_transformer")
        assert test_transformer.transformer_id == "test_transformer"
        assert test_transformer.path == "test.tester"
        assert test_transformer.description == "Test Transformer"

        # update test transformer
        test_transformer = lexy.transformer.update_transformer("test_transformer", path="test.tester2")
        assert test_transformer.transformer_id == "test_transformer"
        assert test_transformer.path == "test.tester2"
        assert test_transformer.description == "Test Transformer"

        # delete test transformer
        response = lexy.transformer.delete_transformer("test_transformer")
        assert response == {"Say": "Transformer deleted!"}

    def test_list_transformers(self):
        transformers = lexy.transformer.list_transformers()
        assert len(transformers) > 0

    @pytest.mark.asyncio
    async def test_alist_transformers(self):
        transformers = await lexy.transformer.alist_transformers()
        assert len(transformers) > 0

    def test_transform_document(self):
        transformer = lexy.transformer.get_transformer("text.embeddings.minilm")
        response = transformer.transform_document({"content": "Hello, world!"})
        assert 'task_id' in response
        assert isinstance(response["result"], list)
        assert all(isinstance(elem, float) for elem in response["result"])
