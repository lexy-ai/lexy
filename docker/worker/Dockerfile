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

# Top 20 largest python packages
RUN echo "Top 20 largest python packages" && export PYSITE=$(python -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())") && du -sh $PYSITE/* | sort -h -r | head -20
# Total size of python packages
RUN echo "Total size of python packages" && export PYSITE=$(python -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())") && du -sh $PYSITE | sort -h -r
# Total size of caches
RUN echo "Total size of caches" && du -sh $HOME/.cache/*
# Keep server alive for debugging
#CMD ["tail", "-f", "/dev/null"]

# Run the start script, it will install any extras and then start the worker
CMD ["/start-worker.sh"]
