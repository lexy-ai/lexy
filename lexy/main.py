import importlib

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from lexy.core.celery_app import create_celery
from lexy.core.config import settings
from lexy.api.router import lexy_api
from lexy.db.init_db import init_db

# import transformer modules so that celery client can find them
for module in settings.app_transformer_imports:
    importlib.import_module(module)


def create_app() -> FastAPI:
    fastapi_app = FastAPI(
        title=settings.TITLE,
        version=settings.VERSION,
        description=settings.DESCRIPTION,
        openapi_prefix=settings.OPENAPI_PREFIX,
        docs_url=settings.DOCS_URL,
        openapi_url=settings.OPENAPI_URL
    )
    fastapi_app.include_router(lexy_api, prefix=settings.API_PREFIX)
    return fastapi_app


# Create FastAPI app
app = create_app()

# Create Celery app
app.celery_app = create_celery()
celery = app.celery_app

# Add CORS middleware
origins = [
    "http://localhost",
    "http://localhost:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # allow all methods
    allow_headers=["*"],  # allow all headers
)


@app.on_event("startup")
def on_startup():
    print('starting app')
    # this subsequent call to init_db() is only used by the index manager to create
    # the default index table (default_text_embeddings) if it doesn't exist - we may
    # be able to remove this call once seed data is added through proper crud endpoints
    init_db()
