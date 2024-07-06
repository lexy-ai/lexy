# Contributing to Lexy

This document provides guidance for developers who want to contribute to the Lexy
codebase.

To set up a development environment, simply follow the instructions in the
[installation guide](installation.md). The command `make install-dev` will install the dev, docs,
and test dependencies.


## Issues

Take a look at open [issues](https://github.com/lexy-ai/lexy/issues) on GitHub if you'd
like to contribute to the project. This is also a great place to submit questions,
feature requests, and bug reports.


## Developer Notes

### Makefile

Many of the common commands for development are available in the
[`Makefile`](https://github.com/lexy-ai/lexy/blob/main/Makefile).

### Running tests

When you open a pull request, tests will run automatically on GitHub Actions. To run
tests locally, you can use the following make command.

```bash
make run-tests
```

This command will run tests for the Lexy server and Lexy Python SDK. If you want to run the tests separately, you can
use the following commands.

```bash
# Run tests for Lexy server
pytest lexy_tests

# Run tests for Python SDK
pytest sdk-python
```

To run tests inside an already running lexy-server container, use the following command.

```bash
make run-tests-docker
```

To create a new lexy-server container and run tests, use the following command. This requires the rest of the stack to
be running.

```bash
make test-lexy-server
```

Note that this option will still mount the current directory, and is not ideal for isolated testing.

### Adding a new migration

To add a new `alembic` migration, first create the migration file.

```bash
# Create a new migration
alembic revision --autogenerate -m "Short description of the migration"
```

Check the migration file in the `alembic/versions` directory and make any necessary changes.

```bash
# Apply the migration
alembic upgrade head

# Check the migration status
alembic current
```

Add the migration file to version control and open a pull request.

### Updating Docker containers

When you pull changes from the repository, you may need to update your local Docker containers. To rebuild the
server and worker containers, and apply database migrations, you can run the following make command:

```bash
make update-dev-containers
```

To rebuild the server and worker containers only (without migrations), run the following.

```bash
docker compose up --build -d --no-deps lexyserver lexyworker
```

If for some reason you need to install the new dependencies without rebuilding your containers, run the following:

```bash
docker exec lexy-server poetry install --no-root -E "lexy_transformers"
docker exec lexy-celeryworker poetry install --no-root -E "lexy_transformers"
```

### Release Docker containers

Docker containers are built for each [release](https://github.com/lexy-ai/lexy/releases) and hosted on GitHub Container
Registry. Packages are available [here](https://github.com/orgs/lexy-ai/packages?repo_name=lexy).

### Pip installing into Docker containers

Sometimes you may need to install a new package into the Docker container, since it's much faster than updating
`pyproject.toml` and rebuilding. You can do this by running the following:

```bash
docker exec lexy-server pip install <your_package>
docker exec lexy-celeryworker pip install <your_package>
```

If you end up keeping the package, make sure to update `pyproject.toml` and recreate the `poetry.lock` file if needed.

```bash
poetry add <your_package>
poetry check
```
