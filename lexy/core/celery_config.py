# source: https://medium.com/cuddle-ai/async-architecture-with-fastapi-celery-and-rabbitmq-c7d029030377
import os
from functools import lru_cache

from kombu import Queue


def route_task(name, args, kwargs, options, task=None, **kw):
    if ":" in name:
        queue, _ = name.split(":")
        return {"queue": queue}
    return {"queue": "celery"}


class BaseConfig:
    CELERY_BROKER_URL: str = os.environ.get("CELERY_BROKER_URL", "amqp://guest:guest@localhost:5672//")
    CELERY_RESULT_BACKEND: str = os.environ.get("CELERY_RESULT_BACKEND",
                                                "db+postgresql://postgres:postgres@localhost:5432/lexy")

    CELERY_TASK_QUEUES: list = (
        # default queue
        Queue("celery", queue_arguments={"x-max-priority": 10}),
        # custom queues
        # Queue("custom_queue_1"),
        # Queue("custom_queue_2"),
    )

    CELERY_TASK_ROUTES = (route_task,)


class DevelopmentConfig(BaseConfig):
    pass


class TestingConfig(BaseConfig):
    CELERY_BROKER_URL = "memory://"
    CELERY_RESULT_BACKEND: str = "db+postgresql://postgres:postgres@localhost:5432/lexy_tests"
    # task_always_eager: bool = True
    # task_eager_propagates: bool = True
    # task_store_eager_result: bool = True
    # task_ignore_result: bool = False


@lru_cache()
def get_settings():
    config_cls_dict = {
        "development": DevelopmentConfig,
        "testing": TestingConfig,
    }
    config_name = os.environ.get("CELERY_CONFIG", "development")
    config_cls = config_cls_dict[config_name]
    return config_cls()


settings = get_settings()
