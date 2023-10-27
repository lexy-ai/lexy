import pytest

from lexy_py.client import LexyClient


lexy = LexyClient()


class TestBindingClient:

    def test_root(self):
        response = lexy.get("/")
        assert response.status_code == 200
        assert response.json() == {"Say": "Hello!"}

    def test_bindings(self):
        # TODO: implement this after setting up mock for testing (do not run against live server)
        pass

    def test_list_bindings(self):
        bindings = lexy.binding.list_bindings()
        assert len(bindings) > 0

    @pytest.mark.asyncio
    async def test_alist_bindings(self):
        bindings = await lexy.binding.alist_bindings()
        assert len(bindings) > 0
