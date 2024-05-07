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

ENV PYTHONPATH="/home/app:/home/app/pipelines:$PYTHONPATH"

# Copy init script
COPY ./docker/worker/start-worker.sh /start-worker.sh
RUN chmod +x /start-worker.sh

# Run the start script, it will install any extras and then start the worker
CMD ["/start-worker.sh"]
