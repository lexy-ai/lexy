import contextlib
import importlib
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from lexy.core.celery_app import create_celery
from lexy.core.config import settings
from lexy.api.deps import index_manager
from lexy.api.router import lexy_api

# Import transformer modules so that celery client can find them
for module in settings.app_transformer_imports:
    importlib.import_module(module)

# Create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@contextlib.asynccontextmanager
async def app_lifespan(app: FastAPI):
    # NOTE: anything run here isn't run by celery workers
    logger.info("Starting FastAPI app")
    index_manager.create_index_models()
    logger.debug("(main.app_lifespan) Created index models")
    logger.debug(f"(main.app_lifespan) {index_manager = }")
    logger.debug(f"(main.app_lifespan) {index_manager.index_models = }")
    # Uncomment the next line to access the index_manager from the app state
    # app.state.index_manager = index_manager
    yield
    logger.info("Stopping FastAPI app")


# Create FastAPI app
app = FastAPI(
    title=settings.TITLE,
    version=settings.VERSION,
    summary=settings.SUMMARY,
    license_info=settings.LICENSE_INFO,
    openapi_prefix=settings.OPENAPI_PREFIX,
    docs_url=settings.DOCS_URL,
    openapi_url=settings.OPENAPI_URL,
    servers=settings.SERVERS,
    lifespan=app_lifespan,
)
app.include_router(lexy_api, prefix=settings.API_PREFIX)

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
