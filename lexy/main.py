from fastapi import FastAPI

from lexy.core.celery_app import create_celery
from lexy.core.config import settings
from lexy.api.router import lexy_api
from lexy.db.init_db import init_db
from lexy.db.session import create_db_and_tables
from lexy.core import events


app = FastAPI(
    title=settings.title,
    version=settings.version,
    description=settings.description,
    openapi_prefix=settings.openapi_prefix,
    docs_url=settings.docs_url,
    openapi_url=settings.openapi_url
)

app.include_router(lexy_api, prefix=settings.api_prefix)
app.celery_app = create_celery()
celery = app.celery_app


# @app.on_event("startup")
# def on_startup():
#     print('starting')
#     init_db()


if __name__ == "__main__":
    @app.on_event("startup")
    async def on_startup():
        print('startup')
        await create_db_and_tables()
