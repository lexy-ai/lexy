# source: https://medium.com/cuddle-ai/async-architecture-with-fastapi-celery-and-rabbitmq-c7d029030377
from celery import current_app as current_celery_app
from celery.result import AsyncResult

from .celery_config import settings


def create_celery():
    celery_app = current_celery_app
    celery_app.config_from_object(settings, namespace='CELERY')
    celery_app.conf.update(task_track_started=True)
    celery_app.conf.update(worker_pool_restarts=True)

    # # list of modules to import when the Celery worker starts.
    # celery_app.conf.update(imports=(
    #     'myapp.tasks',
    # ))

    # serialization settings
    celery_app.conf.update(task_serializer='pickle')
    celery_app.conf.update(result_serializer='pickle')
    celery_app.conf.update(accept_content=[
        'pickle',
        'json',
        'application/json',
        # 'application/x-python-serialize',  # adding for flower
    ])

    # celery_app.conf.update(result_expires=200)
    celery_app.conf.update(result_persistent=True)
    celery_app.conf.update(result_extended=True)

    # celery_app.conf.update(worker_send_task_events=False)
    celery_app.conf.update(worker_send_task_events=True)
    celery_app.conf.update(worker_prefetch_multiplier=1)
    # source: https://rusty-celery.github.io/best-practices/index.html
    celery_app.conf.update(acks_late=True)

    # default priority settings for all queues
    celery_app.conf.update(task_queue_max_priority=10)
    celery_app.conf.update(task_default_priority=5)

    # task routes
    celery_app.conf.task_routes = {
        'lexy.core.celery_tasks': {'queue': 'celery'},
        # 'lexy.transformers.embeddings.text_embeddings': {'queue': 'text:embeddings'},
        # 'lexy.transformers.embeddings.video_embeddings': {'queue': 'video:embeddings'},
    }

    return celery_app


def get_task_info(task_id):
    """
    return task info for the given task_id
    """
    task_result = AsyncResult(task_id)
    result = {
        "task_id": task_id,
        "task_status": task_result.status,
        "task_result": task_result.result
    }
    return result
