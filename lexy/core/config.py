import importlib
import logging
import os
import pkgutil
import sys
from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional

from pydantic import DirectoryPath, field_validator, EmailStr, Field, SecretStr, ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict


# For some reason, this statement initializes logging for the rest of the application.
#  Without it, we don't get log statements for IndexManager.
logging.info("Loading config.py")


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
        if '.' in imp and imp.rsplit('.', 1)[1] == '*':
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
    SECRET_KEY: SecretStr = Field(default="changethis", validation_alias="SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    # Database settings
    POSTGRES_USER: str = Field(default="postgres", validation_alias="POSTGRES_USER")
    POSTGRES_PASSWORD: SecretStr = Field(default="postgres", validation_alias="POSTGRES_PASSWORD")
    POSTGRES_HOST: str = Field(default="localhost", validation_alias="POSTGRES_HOST")
    POSTGRES_DB: str = Field(default="lexy", validation_alias="POSTGRES_DB")
    DB_ECHO_LOG: bool = False

    # User settings
    FIRST_SUPERUSER_EMAIL: EmailStr = Field("lexy@lexy.ai", validation_alias="FIRST_SUPERUSER_EMAIL")
    FIRST_SUPERUSER_PASSWORD: SecretStr = Field("lexy", validation_alias="FIRST_SUPERUSER_PASSWORD")

    # AWS settings
    AWS_ACCESS_KEY_ID: Optional[str] = Field(default=None, validation_alias="AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: Optional[SecretStr] = Field(default=None, validation_alias="AWS_SECRET_ACCESS_KEY")
    AWS_REGION: Optional[str] = Field(default=None, validation_alias="AWS_REGION")

    # Google Cloud settings
    # Path to a file containing JSON credentials for a service account. Using Optional[str] because setting to
    #  Optional[FilePath] triggers a validation error if GOOGLE_APPLICATION_CREDENTIALS is an empty string.
    #  If set to devnull, or to an invalid filepath, GOOGLE_APPLICATION_CREDENTIALS will be set to None.
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = (
        Field(default=None, validation_alias="GOOGLE_APPLICATION_CREDENTIALS")
    )

    @field_validator('GOOGLE_APPLICATION_CREDENTIALS')
    def check_google_application_credentials(cls, value):
        if value == os.path.devnull:
            return None
        if value and not Path(value).is_file():
            logging.warning(f"GOOGLE_APPLICATION_CREDENTIALS file '{value}' does not exist. "
                            f"Setting value to `None`.")
            return None
        return value

    # Storage settings
    DEFAULT_STORAGE_SERVICE: Optional[Literal['s3', 'gcs']] = (
        Field(default="s3", validation_alias="DEFAULT_STORAGE_SERVICE")
    )
    DEFAULT_STORAGE_BUCKET: Optional[str] = Field(default=None, validation_alias="DEFAULT_STORAGE_BUCKET")
    DEFAULT_STORAGE_PREFIX: Optional[str] = Field(default=None, validation_alias="DEFAULT_STORAGE_PREFIX")

    # Default config for Collection objects and images
    COLLECTION_DEFAULT_CONFIG: dict = {
        'store_files': True,
        'generate_thumbnails': True
    }

    @field_validator('COLLECTION_DEFAULT_CONFIG')
    def set_collection_default_config(cls, v: dict, info: ValidationInfo) -> dict:
        if v.get('store_files') is True:
            if not v.get('storage_service'):
                v['storage_service'] = info.data.get('DEFAULT_STORAGE_SERVICE')
            if not v.get('storage_bucket'):
                v['storage_bucket'] = info.data.get('DEFAULT_STORAGE_BUCKET')
            if not v.get('storage_prefix'):
                v['storage_prefix'] = info.data.get('DEFAULT_STORAGE_PREFIX')
        return v

    IMAGE_THUMBNAIL_SIZES: set[tuple] = {
        # (100, 100),
        (200, 200),
    }

    # Transformer settings
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
        'pipelines.*'
    }

    # Pipeline directory (relative to the project root)
    PIPELINE_DIR: DirectoryPath = Field(default="pipelines", validation_alias="PIPELINE_DIR")

    @property
    def sync_database_url(self) -> str:
        return (f"postgresql://"
                f"{self.POSTGRES_USER}"
                f":{self.POSTGRES_PASSWORD.get_secret_value()}"
                f"@{self.POSTGRES_HOST}"
                f"/{self.POSTGRES_DB}")

    @property
    def async_database_url(self) -> str:
        return (f"postgresql+asyncpg://"
                f"{self.POSTGRES_USER}"
                f":{self.POSTGRES_PASSWORD.get_secret_value()}"
                f"@{self.POSTGRES_HOST}"
                f"/{self.POSTGRES_DB}")

    @property
    def app_transformer_imports(self):
        return expand_transformer_imports(self.LEXY_SERVER_TRANSFORMER_IMPORTS)

    @property
    def worker_transformer_imports(self):
        # TODO: Move to a separate property for pipeline imports
        # if self.PIPELINE_DIR:
        #     # Add pipeline imports to the worker transformer imports (i.e., adds 'pipelines.*' to the imports)
        #     pipeline_imports = f'{self.PIPELINE_DIR.name}.*'
        #     expanded_set = self.LEXY_WORKER_TRANSFORMER_IMPORTS.union({pipeline_imports})
        #     return expand_transformer_imports(expanded_set)
        return expand_transformer_imports(self.LEXY_WORKER_TRANSFORMER_IMPORTS)

    @field_validator('PIPELINE_DIR', mode='before')
    @classmethod
    def check_pipeline_dir(cls, value):
        if value:
            pipeline_dir = Path(value).resolve()
            if not pipeline_dir.is_dir():
                raise ValueError(f"Pipeline directory '{pipeline_dir}' does not exist.")
            # log a warning if pipeline_dir is not in the Python path (Celery can't import pipelines)
            if str(pipeline_dir) not in sys.path and str(pipeline_dir) != os.getcwd():
                logging.warning(f"Pipeline directory '{pipeline_dir}' is not in the Python path. "
                                f"Your pipelines may not be imported correctly.")
        return value

    model_config = SettingsConfigDict(case_sensitive=True, env_file='.env', env_file_encoding='utf-8', extra="allow")


class DevelopmentAppSettings(AppSettings):
    pass


class ProductionAppSettings(AppSettings):

    @field_validator('SECRET_KEY')
    @classmethod
    def check_secret_key(cls, value):
        if value.get_secret_value() == "changethis":
            logging.error("Using default value of SECRET_KEY in production settings! "
                          "Change this value to a secure secret key.")
            raise Exception("Using default value of SECRET_KEY in production settings!")
        return value


class TestAppSettings(AppSettings):

    # Database settings
    POSTGRES_DB: str = Field(default="lexy_tests", validation_alias="POSTGRES_TEST_DB")
    DB_ECHO_LOG: bool = False

    # User settings
    # without `env=` argument, this will revert to the environment value of FIRST_SUPERUSER_EMAIL
    FIRST_SUPERUSER_EMAIL: EmailStr = Field("test@lexy.ai", validation_alias="TEST_SUPERUSER_EMAIL")
    FIRST_SUPERUSER_PASSWORD: SecretStr = Field("test", validation_alias="TEST_SUPERUSER_PASSWORD")

    # Storage settings
    DEFAULT_STORAGE_PREFIX: Optional[str] = Field(default="lexy_tests", validation_alias="DEFAULT_STORAGE_PREFIX")
    S3_TEST_BUCKET: Optional[str] = Field(default=None, validation_alias="S3_TEST_BUCKET")
    GCS_TEST_BUCKET: Optional[str] = Field(default=None, validation_alias="GCS_TEST_BUCKET")


@lru_cache()
def get_settings():
    config_cls_dict = {
        "development": DevelopmentAppSettings,
        "testing": TestAppSettings,
    }
    config_name = os.environ.get("LEXY_CONFIG", "development")
    config_cls = config_cls_dict[config_name]
    return config_cls()


settings = get_settings()
