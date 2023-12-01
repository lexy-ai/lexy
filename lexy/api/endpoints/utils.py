import logging
import time

from fastapi import APIRouter, status

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
