import pytest

from lexy_py.client import LexyClient
from lexy_py.exceptions import LexyAPIError, NotFoundError


lexy = LexyClient()


class TestClientExceptions:

    def test_root(self):
        response = lexy.get("/")
        assert response.status_code == 200
        assert response.json() == {"Say": "Hello!"}

    def test_not_found(self):
        with pytest.raises(NotFoundError):
            lexy.collection.get_collection("nonexistent_collection")

    def test_not_found_with_response(self):
        with pytest.raises(NotFoundError) as exc_info:
            lexy.collection.get_collection("nonexistent_collection")
        assert exc_info.value.response_data["status_code"] == 404
        assert exc_info.value.response.status_code == 404
        assert exc_info.value.response.text == '{"detail":"Collection not found"}'

    def test_api_error_with_response(self):
        with pytest.raises(LexyAPIError) as exc_info:
            lexy.document.get_document("not_a_valid_document_id")
        assert exc_info.value.response_data["status_code"] == 500
        assert exc_info.value.response.status_code == 500
        assert exc_info.value.response.text == "Internal Server Error"
