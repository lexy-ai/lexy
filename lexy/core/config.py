import importlib
import os
import pkgutil

from pydantic import BaseConfig


def get_transformer_modules(transformer_pkg: str = 'lexy.transformers'):
    """ Return a list of transformer modules. """
    lexy_transformer_modules = []
    transformer_pkg_m = importlib.import_module(transformer_pkg)
    for m in pkgutil.iter_modules(transformer_pkg_m.__path__,
                                  prefix=transformer_pkg + '.'):
        if not m.ispkg:
            lexy_transformer_modules.append(m.name)
    return lexy_transformer_modules


def expand_transformer_imports(transformer_imports: set[str]) -> set[str]:
    """ Expand transformer imports to include all submodules. """
    expanded_imports = set()
    for imp in transformer_imports:
        if imp.rsplit('.', 1)[1] == '*':
            expanded_imports.update(get_transformer_modules(imp.rsplit('.', 1)[0]))
        else:
            expanded_imports.add(imp)
    return expanded_imports


class GlobalConfig(BaseConfig):

    # API settings
    title: str = "Lexy Server"
    version: str = "1.0.0"
    description: str = "Lexy Server API"
    openapi_prefix: str = ""
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    openapi_url: str = "/openapi.json"
    api_prefix: str = "/api"

    # Database settings
    postgres_user: str = os.environ.get("POSTGRES_USER", "postgres")
    postgres_password: str = os.environ.get("POSTGRES_PASSWORD", "postgres")
    postgres_host: str = os.environ.get("POSTGRES_HOST", "db_postgres")
    # postgres_port: int = int(os.environ.get("POSTGRES_PORT"))
    postgres_db: str = os.environ.get("POSTGRES_DB", "lexy")
    # db_url = os.environ.get("DATABASE_URL")
    db_echo_log: bool = True

    # AWS settings & S3 storage settings
    aws_access_key_id: str = os.environ.get("AWS_ACCESS_KEY_ID", None)
    aws_secret_access_key: str = os.environ.get("AWS_SECRET_ACCESS_KEY", None)
    aws_region: str = os.environ.get("AWS_REGION", None)
    s3_bucket: str = os.environ.get("S3_BUCKET", "rs-lexy-ai-dev-deployments")
    image_thumbnail_sizes: set[tuple] = {
        # (128, 128),
        (256, 256),
    }

    # Celery settings
    lexy_server_transformer_imports = {
        # 'lexy.transformers.*'
        'lexy.transformers.counter',
        'lexy.transformers.embeddings',
        'lexy.transformers.multimodal',
    }
    lexy_worker_transformer_imports = {
        # 'lexy.transformers.*'
        'lexy.transformers.counter',
        'lexy.transformers.embeddings',
        'lexy.transformers.multimodal',
    }

    @property
    def sync_database_url(self) -> str:
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}/{self.postgres_db}"

    @property
    def async_database_url(self) -> str:
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}/{self.postgres_db}"

    @property
    def app_transformer_imports(self):
        return expand_transformer_imports(self.lexy_server_transformer_imports)

    @property
    def worker_transformer_imports(self):
        return expand_transformer_imports(self.lexy_worker_transformer_imports)


settings = GlobalConfig()
