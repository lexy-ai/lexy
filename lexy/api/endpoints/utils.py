import logging
import time

from fastapi import APIRouter, status

from lexy.core.celery_app import get_task_info
from lexy.core.events import celery, restart_celery_worker


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
router = APIRouter()


@router.get("/",
            status_code=status.HTTP_200_OK,
            name="Root")
async def root():
    return {"Say": "Hello!"}


@router.get("/ping",
            status_code=status.HTTP_200_OK,
            name="Ping")
async def pong():
    return {"ping": "pong!"}


@router.get("/celery-conf",
            status_code=status.HTTP_200_OK,
            name="Celery Conf")
async def celery_conf(with_defaults: bool = False):
    return {"Celery conf": celery.control.inspect().conf(with_defaults=with_defaults)}


@router.get("/celery-status",
            status_code=status.HTTP_200_OK,
            name="Celery Status")
async def celery_status():
    return {"Celery status": celery.control.inspect().stats()}


@router.get("/celery-registered-tasks",
            status_code=status.HTTP_200_OK,
            name="Celery Registered Tasks")
async def celery_registered_tasks():
    return {"Celery registered tasks": celery.control.inspect().registered_tasks(),
            "celery.tasks.keys()": sorted(celery.tasks.keys())}


@router.get("/celery-active",
            status_code=status.HTTP_200_OK,
            name="Celery Active")
async def celery_active():
    return {"Celery active": celery.control.inspect().active()}


@router.get("/celery-restart-worker",
            status_code=status.HTTP_200_OK,
            name="Celery Restart Worker")
async def celery_restart_worker(worker_name: str = 'celery@celeryworker'):
    celery_restart_response = restart_celery_worker(worker_name)
    logger.info(f"Response: {celery_restart_response}")
    time.sleep(0.5)
    return {"Celery restart worker": celery_restart_response}


@router.get("/tasks/{task_id}",
            response_model=dict,
            status_code=status.HTTP_200_OK,
            name="get_task_status",
            description="Get task status")
async def get_task_status(task_id: str, verbose: bool = False) -> dict:
    return get_task_info(task_id, verbose=verbose)


@router.get("/tasks",
            response_model=dict,
            status_code=status.HTTP_200_OK,
            name="get_all_tasks",
            description="Get all tasks")
async def get_all_tasks() -> dict:
    return {"active": celery.control.inspect().active(),
            "scheduled": celery.control.inspect().scheduled(),
            "reserved": celery.control.inspect().reserved(),
            "revoked": celery.control.inspect().revoked(),
            "stats": celery.control.inspect().stats(),
            "registered_tasks": celery.control.inspect().registered_tasks(),
            "conf": celery.control.inspect().conf(with_defaults=False)}


@router.get("/index-manager",
            status_code=status.HTTP_200_OK,
            name="get_index_manager")
async def get_index_manager() -> dict:
    from lexy.api.deps import index_manager
    index_models_and_tables = dict(
        (model, index_manager.index_models[model].__table__.name) for model in index_manager.index_models
    )
    return {"index_models_and_tables": index_models_and_tables}


@router.get("/index-manager-celery",
            status_code=status.HTTP_200_OK,
            name="get_index_manager_from_celery")
async def get_index_manager_from_celery() -> dict:
    from lexy.core.celery_tasks import index_manager
    index_models_and_tables = dict(
        (model, index_manager.index_models[model].__table__.name) for model in index_manager.index_models
    )
    return {"index_models_and_tables": index_models_and_tables}
