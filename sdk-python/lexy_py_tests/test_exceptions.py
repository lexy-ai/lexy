import pytest

from lexy_py.exceptions import LexyAPIError, NotFoundError


class TestClientExceptions:
    def test_root(self, lx_client):
        response = lx_client.get("/")
        assert response.status_code == 200
        assert response.json() == {"Say": "Hello!"}

    def test_not_found(self, lx_client):
        with pytest.raises(NotFoundError):
            lx_client.collection.get_collection(
                collection_name="nonexistent_collection"
            )

    def test_not_found_with_response(self, lx_client):
        with pytest.raises(NotFoundError) as exc_info:
            lx_client.collection.get_collection(
                collection_name="nonexistent_collection"
            )
        assert (
            exc_info.value.response_data["status_code"] == 404
        ), exc_info.value.response_data
        assert exc_info.value.response.status_code == 404
        assert exc_info.value.response.text == '{"detail":"Collection not found"}'

    def test_api_error_with_response(self, lx_client):
        # NOTE: this requires TestClient to have the argument
        #   `raise_server_exceptions=False`
        #   https://github.com/tiangolo/fastapi/discussions/9007
        with pytest.raises(LexyAPIError) as exc_info:
            lx_client.document.get_document("not_a_valid_document_id")
        assert (
            exc_info.value.response_data["status_code"] == 500
        ), exc_info.value.response_data
        assert exc_info.value.response.status_code == 500
        assert exc_info.value.response.text == "Internal Server Error"
