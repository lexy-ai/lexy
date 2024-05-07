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

# check current directory
RUN pwd
RUN ls -lah

ARG ENVIRONMENT=development

RUN pip install poetry
RUN poetry config virtualenvs.create false

# copy source code
#COPY . ./
COPY lexy ./lexy
COPY pipelines ./pipelines
COPY lexy_tests ./lexy_tests
COPY README.md ./
RUN ls -lah

# TODO: switch to --no-root install followed by install from git
#poetry install --no-root -E "lexy_transformers";

RUN if [ "$ENVIRONMENT" = "development" ]; \
      then \
        poetry install --no-root -E "lexy_transformers"; \
      else \
        poetry install -E "lexy_transformers"; \
    fi

ENV PYTHONPATH="/home/app:/home/app/pipelines:$PYTHONPATH"

# Copy init script
COPY ./docker/server/start-server.sh /start-server.sh
RUN chmod +x /start-server.sh

# Run the start script, it will check for a './lexy/prestart.sh' script (e.g., for DB initialization)
CMD ["/start-server.sh"]
# uncomment for testing
#CMD ["tail", "-f", "/dev/null"]
