FROM python:3.11

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update

RUN apt-get install -y \
    build-essential \
    curl \
    python3 \
    python3-dev \
    python3-venv

WORKDIR /home/app
COPY ../../pyproject.toml ./poetry.lock* ./

ARG ENVIRONMENT=development

RUN pip install poetry
RUN poetry config virtualenvs.create false

# copy source code
#COPY . ./
COPY lexy ./lexy
COPY pipelines ./pipelines
COPY lexy_tests ./lexy_tests
COPY README.md ./
COPY sdk-python ./sdk-python
RUN ls -lah

# TODO: switch to --no-root install followed by install from git
#poetry install --no-root -E "lexy_transformers";

RUN if [ "$ENVIRONMENT" = "development" ]; \
      then \
        poetry install --no-root -E "lexy_transformers"; \
      else \
        poetry install -E "lexy_transformers"; \
        cd ./sdk-python && poetry install; \
    fi

#ENV PYTHONPATH="/home/app:/home/app/pipelines:$PYTHONPATH"
ENV DOCKER=true \
    CELERY_BROKER_URL=amqp://guest:guest@queue:5672// \
    CELERY_BROKER_API_URL=http://guest:guest@queue:15672/api/vhost \
    CELERY_RESULT_BACKEND=db+postgresql://postgres:postgres@db_postgres/lexy \
    C_FORCE_ROOT=true \
    POSTGRES_USER=postgres \
    POSTGRES_PASSWORD=postgres \
    POSTGRES_DB=lexy \
    POSTGRES_HOST=db_postgres \
    PIPELINE_DIR=/home/app/pipelines \
    PYTHONPATH=/home/app:/home/app/pipelines \
    # Unset GOOGLE_APPLICATION_CREDENTIALS for the celery worker \
    GOOGLE_APPLICATION_CREDENTIALS=""

# Copy init script
COPY ./docker/worker/start-worker.sh /start-worker.sh
RUN chmod +x /start-worker.sh

# Run the start script, it will install any extras and then start the worker
CMD ["/start-worker.sh"]
