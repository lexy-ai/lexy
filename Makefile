define VENV_ERROR_MESSAGE
Please activate a virtual environment before running this command.\nFrom the root of project directory, run the following:\n\n$ python3 -m venv venv\n$ source venv/bin/activate\n
endef

check-virtualenv:
	@if [ -z "$(VIRTUAL_ENV)" ]; then \
		echo "$(VENV_ERROR_MESSAGE)"; \
		exit 1; \
	fi

check-pyversion:
	@if [ "$(shell python -c 'import sys; print(sys.version_info >= (3, 11))')" = "False" ]; then \
		echo "Lexy requires Python 3.11 or higher."; \
		exit 1; \
	fi

check-env: check-virtualenv check-pyversion

serve-docs: check-env
	mkdocs serve -f docs/mkdocs.yml

recreate-queues:
	docker exec lexy-queue rabbitmqctl stop_app
	docker exec lexy-queue rabbitmqctl reset
	docker exec lexy-queue rabbitmqctl start_app

inspect-celery:
	docker exec lexy-celeryworker celery inspect active -t 10.0

install-dev: check-env
	# install poetry
	pip install poetry
	# install dev dependencies and extras
	poetry install --no-root --with test,docs,dev -E "lexy_transformers"

	# install lexy in editable mode
	pip install -e .
	pip install -e sdk-python

	# create .env file if it doesn't exist
	cp -n .env.example .env

build-dev:
	# build docker images
	docker-compose up --build -d

update-dev-env: check-env
	# update dev dependencies and extras
	poetry install --no-root --with test,docs,dev -E "lexy_transformers"

restart-dev-containers:
	docker-compose restart lexyserver lexyworker

rebuild-dev-containers:
	# rebuild lexyserver and lexyworker
	docker-compose up --build -d --no-deps lexyserver lexyworker

run-migrations:
	# run DB migrations
	alembic upgrade head

update-dev-containers: rebuild-dev-containers run-migrations

update-dev: update-dev-env update-dev-containers

update-doc-reqs: check-env
	# update docs/requirements-docs.txt
	poetry export --only=docs --without-hashes -f requirements.txt --output docs/requirements-docs.txt

run-tests: check-env
	pytest lexy_tests
	pytest sdk-python
