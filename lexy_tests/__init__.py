import os
from importlib.util import find_spec

if find_spec("pytest") is None:
    raise ImportError(
        "The 'lexy_tests' package requires additional dependencies. "
        "Please install them using 'pip install lexy[tests]'."
    )

os.environ["LEXY_CONFIG"] = "testing"
os.environ["CELERY_CONFIG"] = "testing"

from lexy_tests.conftest import async_client, client, test_settings  # noqa: E402

__all__ = [
    "async_client",
    "client",
    "test_settings"
]
