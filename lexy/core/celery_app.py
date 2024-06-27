# source: https://medium.com/cuddle-ai/async-architecture-with-fastapi-celery-and-rabbitmq-c7d029030377
from celery import Celery
from celery.result import AsyncResult

from lexy.core.config import settings as lexy_settings
from lexy.core.celery_config import settings as celery_settings


def create_celery(celery_settings=celery_settings, lexy_settings=lexy_settings):
    celery_app = Celery()
    celery_app.config_from_object(celery_settings, namespace="CELERY")

    # list of modules to import when the Celery worker starts.
    # celery_app.conf.update(imports=(
    #     'myapp.tasks',
    # ))
    # TODO: why is 'lexy.core.celery_tasks' not included in imports?
    celery_app.conf.update(imports=list(lexy_settings.worker_transformer_imports))
    celery_app.conf.update(include=lexy_settings.worker_transformer_imports)

    return celery_app


def get_task_info(task_id, verbose: bool = False) -> dict:
    """Return task info for the given task_id."""
    task_result = AsyncResult(task_id)
    result = {
        "id": task_id,
        "name": task_result.name,
        "status": task_result.status,
        "date_done": task_result.date_done,
        "retries": task_result.retries,
        "worker": task_result.worker,
        "queue": task_result.queue,
        "parent": task_result.parent,
        "children": task_result.children,
        "info": task_result.info,
    }
    if verbose:
        result["result"] = task_result.result
        result["traceback"] = task_result.traceback
        result["args"] = task_result.args
        result["kwargs"] = task_result.kwargs
    return result
