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
RUN if [ "$ENVIRONMENT" = "development" ]; then poetry install --no-root -E "lexy_transformers"; else poetry install -E "lexy_transformers"; fi

ENV PYTHONPATH="/home/app:/home/app/pipelines:$PYTHONPATH"

# Copy init script
COPY ./docker/worker/start-worker.sh /start-worker.sh
RUN chmod +x /start-worker.sh

# Run the start script, it will install any extras and then start the worker
CMD ["/start-worker.sh"]
