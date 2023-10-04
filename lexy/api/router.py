from fastapi import APIRouter

from lexy.api.endpoints import (
    bindings,
    collections,
    documents,
    embeddings,
    indexes,
    index_records,
    transformers,
    utils
)


lexy_api = APIRouter()

lexy_api.include_router(bindings.router, tags=["bindings"])
lexy_api.include_router(collections.router, tags=["collections"])
lexy_api.include_router(documents.router, tags=["documents"])
lexy_api.include_router(embeddings.router, tags=["embeddings"])
lexy_api.include_router(indexes.router, tags=["indexes"])
lexy_api.include_router(index_records.router, tags=["index_records"])
lexy_api.include_router(transformers.router, tags=["transformers"])
lexy_api.include_router(utils.router, tags=["utils"])
