# source: https://medium.com/cuddle-ai/async-architecture-with-fastapi-celery-and-rabbitmq-c7d029030377
import os

from kombu import Queue


# TODO: fix or delete this
def route_task(name, args, kwargs, options, task=None, **kw):
    if ":" in name:
        queue, _ = name.split(":")
        return {"queue": queue}
    return {"queue": "celery"}


class BaseConfig:
    # TODO: these should be constructed from lexy_settings
    broker_url: str = os.environ.get(
        "CELERY_BROKER_URL", "amqp://guest:guest@localhost:5672//"
    )
    pg_host = os.environ.get("POSTGRES_HOST", "localhost")
    result_backend: str = os.environ.get(
        "CELERY_RESULT_BACKEND",
        f"db+postgresql://postgres:postgres@{pg_host}:5432/lexy",
    )

    broker_connection_retry_on_startup = True
    task_track_started = True

    # Queues
    task_queues: list = (
        # default queue
        Queue("celery", queue_arguments={"x-max-priority": 10}),
        # custom queues
        # Queue("custom_queue_1"),
        # Queue("custom_queue_2"),
    )

    # Default priority settings for all queues
    task_queue_max_priority = 10
    task_default_priority = 5

    # Task routes
    task_routes = {
        "lexy.core.celery_tasks": {"queue": "celery"},
        # 'lexy.transformers.embeddings.text_embeddings': {'queue': 'text:embeddings'},
        # 'lexy.transformers.embeddings.video_embeddings': {'queue': 'video:embeddings'},
    }
    # task_routes = (route_task,)

    # Serialization settings
    task_serializer = "pickle"
    result_serializer = "pickle"
    accept_content = [
        "pickle",
        "json",
        "application/json",
        # 'application/x-python-serialize',  # adding for flower
    ]

    # Result settings
    result_persistent = True
    result_extended = True

    # Worker settings
    # list of modules to import when the Celery worker starts -- these are currently set in
    #  `lexy.celery_app.create_celery`.
    # imports = (
    #     'myapp.tasks',
    #     'lexy.core.celery_tasks',
    #     list(lexy_settings.worker_transformer_imports)
    # )
    # include = lexy_settings.worker_transformer_imports
    worker_pool_restarts = True
    worker_send_task_events = True
    worker_prefetch_multiplier = 1
    # source: https://rusty-celery.github.io/best-practices/index.html
    acks_late = True


class DevelopmentConfig(BaseConfig):
    pass


class TestingConfig(BaseConfig):
    # WARNING: These settings will be ignored in favor of any environment variables, even if set
    #  explicitly. See https://github.com/celery/celery/issues/4284.
    #  To override these settings at test time, use `pytest.ini_options` in pyproject.toml, or
    #  overwrite value of env var in lexy_tests/conftest.py.
    broker_url: str = "memory://"
    # TODO: these should be constructed from lexy_settings
    pg_host = os.environ.get("POSTGRES_HOST", "localhost")
    result_backend: str = f"db+postgresql://postgres:postgres@{pg_host}:5432/lexy_tests"


def get_settings():
    config_cls_dict = {
        "development": DevelopmentConfig,
        "testing": TestingConfig,
    }
    config_name = os.environ.get("CELERY_CONFIG", "development")
    config_cls = config_cls_dict[config_name]
    return config_cls()


settings = get_settings()
