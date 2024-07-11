import pytest

from lexy_py.exceptions import LexyAPIError
from lexy_py.transformer.models import Transformer


class TestTransformerClient:
    def test_root(self, lx_client):
        response = lx_client.get("/")
        assert response.status_code == 200
        assert response.json() == {"Say": "Hello!"}

    def test_create_transformer(self, lx_client, celery_app, celery_worker):
        assert "lexy.transformers.new_transformer" not in celery_app.tasks

        # register new transformer
        from lexy.transformers import lexy_transformer

        @lexy_transformer("new_transformer")
        def new_transformer(document):
            return document.content

        celery_worker.reload()
        assert "lexy.transformers.new_transformer" in celery_app.tasks

        # create new transformer
        transformer = lx_client.create_transformer(
            transformer_id="new_transformer",
            path="new.test.transformer",
            description="New Test Transformer",
        )
        assert transformer.transformer_id == "new_transformer"
        assert transformer.path == "new.test.transformer"
        assert transformer.description == "New Test Transformer"

        # transform document
        response = transformer.transform_document({"content": "Hello, world!"})
        assert "task_id" in response
        assert response["result"] == "Hello, world!"

        # delete new transformer
        response = lx_client.delete_transformer("new_transformer")
        assert response.get("msg") == "Transformer deleted"
        assert response.get("transformer_id") == "new_transformer"

    def test_transformers(self, lx_client, celery_app, celery_worker):
        # get all transformers
        transformers = lx_client.list_transformers()
        assert len(transformers) > 0

        # register test transformer
        from lexy.transformers import lexy_transformer

        @lexy_transformer("test_transformer")
        def test_transformer(document):
            return document.content

        # create test transformer
        transformer = lx_client.create_transformer(
            transformer_id="test_transformer",
            path="test.tester",
            description="Test Transformer",
        )
        assert transformer.transformer_id == "test_transformer"
        assert transformer.path == "test.tester"
        assert transformer.description == "Test Transformer"

        # get test transformer
        transformer = lx_client.get_transformer("test_transformer")
        assert transformer.transformer_id == "test_transformer"
        assert transformer.path == "test.tester"
        assert transformer.description == "Test Transformer"

        # update test transformer
        transformer = lx_client.update_transformer(
            "test_transformer", path="test.tester2"
        )
        assert transformer.transformer_id == "test_transformer"
        assert transformer.path == "test.tester2"
        assert transformer.description == "Test Transformer"

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
        assert "task_id" in response
        assert isinstance(response["result"], list)
        assert all(isinstance(elem, float) for elem in response["result"])

    def test_transform_document_error(self, lx_client, celery_app, celery_worker):
        # register new transformer
        from lexy.transformers import lexy_transformer

        @lexy_transformer("divide_by_zero")
        def divide_by_zero(document):
            e = 1 / 0  # noqa: F841
            return document.content

        celery_worker.reload()
        assert "lexy.transformers.divide_by_zero" in celery_app.tasks

        # create new transformer
        transformer = lx_client.create_transformer(
            transformer_id="divide_by_zero",
            description="Divide by Zero",
        )
        assert transformer.transformer_id == "divide_by_zero"
        assert transformer.description == "Divide by Zero"

        response = transformer.transform_document({"content": "Hello, world!"})
        assert "task_id" in response
        assert response["error"] == "division by zero"
        assert "ZeroDivisionError" in response["traceback"]

    def test_create_existing_transformer(self, lx_client):
        with pytest.raises(LexyAPIError) as exc_info:
            lx_client.create_transformer(
                transformer_id="text.embeddings.minilm",
                path="test.tester",
                description="Existing Transformer",
            )
        assert isinstance(exc_info.value, LexyAPIError)
        assert (
            exc_info.value.response_data["status_code"] == 400
        ), exc_info.value.response_data
        assert exc_info.value.response.status_code == 400
        assert (
            exc_info.value.response.json()["detail"]
            == "Transformer with that ID already exists"
        )

    def test_create_transformer_without_celery_task(
        self, lx_client, celery_app, celery_worker
    ):
        with pytest.raises(LexyAPIError) as exc_info:
            lx_client.create_transformer(
                transformer_id="no_celery_task",
                path="test.tester",
                description="Test Transformer",
            )
        assert isinstance(exc_info.value, LexyAPIError)
        assert (
            exc_info.value.response_data["status_code"] == 400
        ), exc_info.value.response_data
        assert exc_info.value.response.status_code == 400
        assert (
            exc_info.value.response.json()["detail"]
            == "Could not find Celery task 'lexy.transformers.no_celery_task'"
        )


class TestTransformerModel:
    def test_create_transformer(self):
        transformer = Transformer(transformer_id="test_transformer")
        assert transformer.transformer_id == "test_transformer"
        transformer = Transformer(transformer_id="test-transformer")
        assert transformer.transformer_id == "test-transformer"
        transformer = Transformer(transformer_id="test.transformer")
        assert transformer.transformer_id == "test.transformer"

    def test_create_transformer_with_invalid_id(self):
        with pytest.raises(ValueError):
            Transformer(transformer_id="", description="Test Transformer")  # blank
        with pytest.raises(ValueError):
            Transformer(
                transformer_id="test transformer", description="Test Transformer"
            )  # space
        with pytest.raises(ValueError):
            Transformer(
                transformer_id="_test", description="Test Transformer"
            )  # starts with underscore
        with pytest.raises(ValueError):
            Transformer(
                transformer_id="1abc", description="Test Transformer"
            )  # starts with number
        with pytest.raises(ValueError):
            Transformer(
                transformer_id="transformer" * 30, description="Test Transformer"
            )  # too long
