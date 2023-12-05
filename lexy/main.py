import importlib

from fastapi import FastAPI

from lexy.core.celery_app import create_celery
from lexy.core.config import settings
from lexy.api.router import lexy_api
from lexy.db.init_db import init_db

# import transformer modules so that celery client can find them
for module in settings.app_transformer_imports:
    importlib.import_module(module)


def create_app() -> FastAPI:
    fastapi_app = FastAPI(
        title=settings.title,
        version=settings.version,
        description=settings.description,
        openapi_prefix=settings.openapi_prefix,
        docs_url=settings.docs_url,
        openapi_url=settings.openapi_url
    )
    fastapi_app.include_router(lexy_api, prefix=settings.api_prefix)
    return fastapi_app


app = create_app()
app.celery_app = create_celery()
celery = app.celery_app


@app.on_event("startup")
def on_startup():
    print('starting app')
    # this subsequent call to init_db() is only used by the index manager to create
    # the default index table (default_text_embeddings) if it doesn't exist - we may
    # be able to remove this call once seed data is added through proper crud endpoints
    init_db()
