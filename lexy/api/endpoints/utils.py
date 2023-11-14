from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession

from lexy.db.seed import add_sample_data_to_db
from lexy.db.session import get_session, create_db_and_tables, recreate_db_and_tables
from lexy.core.events import celery


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


@router.get("/create-db",
            status_code=status.HTTP_200_OK,
            name="Create database")
async def create_db():
    await create_db_and_tables()
    return {"Say": "Database created!"}


@router.get("/recreate-db",
            status_code=status.HTTP_200_OK,
            name="Recreate Database")
async def recreate_db():
    await recreate_db_and_tables()
    return {"Say": "Database recreated!"}


@router.post("/add-sample-data",
             status_code=status.HTTP_200_OK,
             name="Add Sample Data",
             description="Seed the database with sample data")
async def add_sample_data(session: AsyncSession = Depends(get_session)):
    await add_sample_data_to_db(session=session)
    return {"Say": "Sample data added!"}


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
