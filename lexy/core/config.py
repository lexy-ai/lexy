import importlib
import pkgutil

from pydantic import BaseSettings, EmailStr, Field, SecretStr, validator


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


class AppSettings(BaseSettings):

    # API settings
    TITLE: str = "Lexy Server"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Lexy Server API"
    OPENAPI_PREFIX: str = ""
    DOCS_URL: str = "/docs"
    REDOC_URL: str = "/redoc"
    OPENAPI_URL: str = "/openapi.json"
    API_PREFIX: str = "/api"

    # Security settings
    # Uncomment the line below if you want to generate a new secret key every time the server restarts. Then, to use a
    #  fixed key, you would simply set the value of SECRET_KEY in your .env file. If you uncomment the next line,
    #  add `import secrets` to the top of this file.
    # SECRET_KEY: SecretStr = Field(default_factory=secrets.token_urlsafe, env="SECRET_KEY")
    SECRET_KEY: SecretStr = Field(default="changethis", env="SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    # Database settings
    POSTGRES_USER: str = Field(default="postgres", env="POSTGRES_USER")
    POSTGRES_PASSWORD: SecretStr = Field(default="postgres", env="POSTGRES_PASSWORD")
    POSTGRES_HOST: str = Field(default="localhost", env="POSTGRES_HOST")
    POSTGRES_DB: str = Field(default="lexy", env="POSTGRES_DB")
    DB_ECHO_LOG: bool = False

    # User settings
    FIRST_SUPERUSER_EMAIL: EmailStr = Field("lexy@lexy.ai", env="FIRST_SUPERUSER_EMAIL")
    FIRST_SUPERUSER_PASSWORD: SecretStr = Field("lexy", env="FIRST_SUPERUSER_PASSWORD")

    # AWS settings & S3 storage settings
    AWS_ACCESS_KEY_ID: str = Field(default=None, env="AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: SecretStr = Field(default=None, env="AWS_SECRET_ACCESS_KEY")
    AWS_REGION: str = Field(default=None, env="AWS_REGION")
    S3_BUCKET: str = Field(default=None, env="S3_BUCKET")

    # Default config for Collection objects and images
    COLLECTION_DEFAULT_CONFIG: dict = {
        'store_files': True,
        'generate_thumbnails': True,
    }
    IMAGE_THUMBNAIL_SIZES: set[tuple] = {
        # (100, 100),
        (200, 200),
    }

    # Celery settings
    LEXY_SERVER_TRANSFORMER_IMPORTS: set[str] = {
        # 'lexy.transformers.*'
        'lexy.transformers.counter',
        'lexy.transformers.embeddings',
        'lexy.transformers.multimodal',
        'lexy.transformers.openai',
    }
    LEXY_WORKER_TRANSFORMER_IMPORTS: set[str] = {
        # 'lexy.transformers.*'
        'lexy.transformers.counter',
        'lexy.transformers.embeddings',
        'lexy.transformers.multimodal',
        'lexy.transformers.openai',
    }

    @property
    def sync_database_url(self) -> str:
        return (f"postgresql://"
                f"{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD.get_secret_value()}"
                f"@{self.POSTGRES_HOST}"
                f"/{self.POSTGRES_DB}")

    @property
    def async_database_url(self) -> str:
        return (f"postgresql+asyncpg://"
                f"{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD.get_secret_value()}"
                f"@{self.POSTGRES_HOST}"
                f"/{self.POSTGRES_DB}")

    @property
    def app_transformer_imports(self):
        return expand_transformer_imports(self.LEXY_SERVER_TRANSFORMER_IMPORTS)

    @property
    def worker_transformer_imports(self):
        return expand_transformer_imports(self.LEXY_WORKER_TRANSFORMER_IMPORTS)

    @validator('SECRET_KEY')
    def check_secret_key(cls, value):
        if value.get_secret_value() == "changethis":
            import logging
            logging.warning("Using default value of SECRET_KEY. Do NOT use this value for production!")
        return value

    class Config:
        case_sensitive = True
        env_file = '.env'
        env_file_encoding = 'utf-8'


class TestAppSettings(AppSettings):

    # Database settings
    POSTGRES_DB: str = Field(default="lexy_tests", env="POSTGRES_TEST_DB")
    DB_ECHO_LOG: bool = False

    # User settings
    # without `env=` argument, this will revert to the environment value of FIRST_SUPERUSER_EMAIL
    FIRST_SUPERUSER_EMAIL: EmailStr = Field("test@lexy.ai", env="TEST_SUPERUSER_EMAIL")
    FIRST_SUPERUSER_PASSWORD: SecretStr = Field("test", env="TEST_SUPERUSER_PASSWORD")


settings = AppSettings()
