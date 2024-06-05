import os

try:
    import pytest
except ImportError as e:
    raise ImportError(
        "The 'lexy_tests' package requires additional dependencies. "
        "Please install them using 'pip install lexy[tests]'."
    ) from e

os.environ["LEXY_CONFIG"] = "testing"  # noqa: E402
os.environ["CELERY_CONFIG"] = "testing"  # noqa: E402

from lexy_tests.conftest import async_client, client, test_settings
