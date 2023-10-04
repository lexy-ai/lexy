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

#RUN python3 -m venv .venv


WORKDIR /home/app
COPY ../../pyproject.toml ./poetry.lock* ./

#RUN #pip install -e .
RUN pip install poetry
RUN poetry config virtualenvs.create false
RUN poetry install --no-root -E "lexy_transformers"

#ENV PATH="/.venv/bin:$PATH"

#CMD ["poetry", "run", "uvicorn", "lexy.main:app", "--host", "0.0.0.0", "--port", "9900", "--reload"]
