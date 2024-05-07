FROM python:3.11

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VERSION=1.8.2 \
    POETRY_CACHE_DIR="$HOME/.cache/pypoetry"

RUN set -ex && \
    apt-get update

RUN set -ex && \
    apt-get install -y \
    build-essential \
    curl \
    python3 \
    python3-dev \
    python3-venv

WORKDIR /home/app
COPY ../../pyproject.toml ./poetry.lock* ./

ARG ENVIRONMENT=development

RUN pip install "poetry==$POETRY_VERSION"
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --no-root -E "lexy_transformers" && rm -rf $POETRY_CACHE_DIR;

# copy source code
COPY lexy ./lexy
COPY lexy_tests ./lexy_tests
COPY pipelines ./pipelines
COPY README.md ./
COPY sdk-python ./sdk-python

RUN if [ "$ENVIRONMENT" = "development" ]; \
      then \
        echo "development install, skipping install of 'lexy' and 'lexy-py'"; \
      else \
        echo "installing 'lexy'"; \
        poetry install --only-root -E "lexy_transformers"; \
        echo "installing 'lexy-py'"; \
        cd ./sdk-python && poetry install; \
    fi

ENV DOCKER=true \
    POSTGRES_USER=postgres \
    POSTGRES_PASSWORD=postgres \
    POSTGRES_DB=lexy \
    POSTGRES_HOST=db_postgres \
    POSTGRES_TEST_DB=lexy_tests \
    CELERY_BROKER_URL=amqp://guest:guest@queue:5672// \
    CELERY_RESULT_BACKEND=db+postgresql://postgres:postgres@db_postgres/lexy \
    PIPELINE_DIR=/home/app/pipelines \
    PYTHONPATH=/home/app:/home/app/pipelines \
    GOOGLE_APPLICATION_CREDENTIALS=/run/secrets/gcp_credentials

# Copy init script
COPY ./docker/server/start-server.sh /start-server.sh
RUN chmod +x /start-server.sh

# Run the start script, it will check for a './lexy/prestart.sh' script (e.g., for DB initialization)
CMD ["/start-server.sh"]
