define VENV_ERROR_MESSAGE
Please activate a virtualenv (or Conda env) before running this command.\nFrom the root of project directory, run the following:\n\n$ python3 -m venv venv\n$ source venv/bin/activate\n
endef

check-virtualenv:
	@if [ -z "$(VIRTUAL_ENV)" ] && [ -z "$(CONDA_PREFIX)" ]; then \
		echo "$(VENV_ERROR_MESSAGE)"; \
		exit 1; \
	fi

check-pyversion:
	@if [ "$(shell python -c 'import sys; print(sys.version_info >= (3, 11))')" = "False" ]; then \
		echo "Lexy requires Python 3.11 or higher."; \
		exit 1; \
	fi

check-env: check-virtualenv check-pyversion

check-lexy-server:
	@echo "Checking if lexy-server container is running..."
	@docker inspect --format='{{.State.Running}}' lexy-server | grep -q true || (echo "lexy-server container is not running. Please start the container and try again." && exit 1)

export-openapi-for-docs: check-env
	python scripts/export_openapi.py

serve-docs: check-env
	mkdocs serve -f docs/mkdocs.yml

recreate-queues:
	docker exec lexy-queue rabbitmqctl stop_app
	docker exec lexy-queue rabbitmqctl reset
	docker exec lexy-queue rabbitmqctl start_app

inspect-celery:
	docker exec lexy-celeryworker celery inspect active -t 10.0

install-dev: check-env
	# Create .env file if it doesn't exist
	cp -n .env.example .env
	# Install poetry
	pip install poetry
	poetry config virtualenvs.create false
	# Install dev dependencies and extras
	poetry install --no-root --with test,docs,dev -E "lexy_transformers"
	# Install lexy in editable mode
	pip install -e .
	pip install -e sdk-python
	lexy init --no-input

build-dev:
	# Build docker images
	docker compose up --build -d

update-dev-env: check-env
	# Update dev dependencies and extras
	poetry install --no-root --with test,docs,dev -E "lexy_transformers"

restart-dev-containers:
	docker compose restart lexyserver lexyworker

rebuild-dev-containers:
	# Rebuild lexyserver and lexyworker
	docker compose up --build -d --no-deps lexyserver lexyworker

# NOTE: Migrations will be applied as part of rebuild-dev-containers if they are uncommented in `lexy/prestart.sh`
#   keeping this target for manual migration runs during development
run-migrations:
	# Run DB migrations
	alembic upgrade head

# See the note on `run-migrations` target as to why this target doesn't also run migrations
update-dev-containers: rebuild-dev-containers

update-dev: update-dev-env update-dev-containers

update-doc-reqs: check-env
	# Update docs/requirements-docs.txt
	poetry export --only=docs --without-hashes -f requirements.txt --output docs/requirements-docs.txt

run-tests: check-env
	pytest lexy_tests
	pytest sdk-python

run-tests-docker: check-lexy-server
	# Run tests inside of an already running lexy-server container
	docker compose exec -it lexyserver pytest lexy_tests
	docker compose exec -it lexyserver pytest sdk-python

# FIXME: this is still mounting the local directory to `/home/app` - need to remove using docker-compose.test.yml
test-lexy-server:
	# Create a new server container and run tests - this requires the rest of the stack to be running
	docker compose run -it --rm --no-deps lexyserver sh -c "pytest lexy_tests && pytest sdk-python"

test-lexy-stack:
	@echo "Not yet implemented"
	exit 1
    # Create a new test stack, run tests, and remove the stack
	docker compose -f docker-compose.test.yml up -d
	docker compose -f docker-compose.test.yml exec lexyserver sh -c "pytest lexy_tests && pytest sdk-python"
	docker compose -f docker-compose.test.yml down

drop-db-tables:
	# Stop the server
	docker compose stop lexyserver lexyworker
	# Copy the drop_tables function to the postgres container
	docker cp scripts/drop_tables.sql lexy-postgres:/tmp/drop_tables.sql
	# Execute the script to drop all tables in public schema
	docker exec lexy-postgres psql -U postgres -d lexy -f /tmp/drop_tables.sql
	# Restart the server
	docker compose start lexyserver lexyworker
