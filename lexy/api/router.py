from fastapi import APIRouter

from lexy.api.endpoints import (
    bindings,
    collections,
    documents,
    indexes,
    index_records,
    login,
    transformers,
    users,
    utils
)


lexy_api = APIRouter()

lexy_api.include_router(bindings.router, tags=["bindings"])
lexy_api.include_router(collections.router, tags=["collections"])
lexy_api.include_router(documents.router, tags=["documents"])
lexy_api.include_router(indexes.router, tags=["indexes"])
lexy_api.include_router(index_records.router, tags=["index_records"])
lexy_api.include_router(login.router, tags=["login"])
lexy_api.include_router(transformers.router, tags=["transformers"])
lexy_api.include_router(users.router, tags=["users"])
lexy_api.include_router(utils.router, tags=["utils"])
