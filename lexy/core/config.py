import os
from pydantic import BaseConfig


class GlobalConfig(BaseConfig):
    title: str = "Lexy Server"
    version: str = "1.0.0"
    description: str = "Lexy Server API"
    openapi_prefix: str = ""
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    openapi_url: str = "/openapi.json"
    api_prefix: str = "/api"

    postgres_user: str = os.environ.get("POSTGRES_USER", "postgres")
    postgres_password: str = os.environ.get("POSTGRES_PASSWORD", "postgres")
    postgres_host: str = os.environ.get("POSTGRES_HOST", "db_postgres")
    # postgres_port: int = int(os.environ.get("POSTGRES_PORT"))
    postgres_db: str = os.environ.get("POSTGRES_DB", "lexy")
    # db_url = os.environ.get("DATABASE_URL")
    db_echo_log: bool = True

    @property
    def sync_database_url(self) -> str:
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}/{self.postgres_db}"

    @property
    def async_database_url(self) -> str:
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}/{self.postgres_db}"


settings = GlobalConfig()
