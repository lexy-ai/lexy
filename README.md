# Lexy

Welcome to Lexy!
 
## Development

### Clone the repo

```Shell
git clone https://github.com/shabani1/lexy.git
```

### Install dependencies

```Shell
# create a virtualenv
python -m venv venv 
source venv/bin/activate

# install poetry
pip install poetry

# install dev dependencies and extras
poetry install --no-root --with test,docs -E "lexy_transformers"

# install lexy in editable mode
pip install -e .

# build docker images
docker-compose up --build -d
```

### Where to find services

| Service      | URL                        | Notes                                |
|--------------|----------------------------|--------------------------------------|
| Lexy API     | http://localhost:9900/docs | Swagger API docs                     |
| Flower       | http://localhost:5556      | Celery task monitor                  |
| RabbitMQ     | http://localhost:15672     | Username: `guest`, Password: `guest` |
| Project docs | http://localhost:8000      | Run `make serve-docs`                |


### PyCharm issues

If your virtualenv keeps getting bjorked by PyCharm, rerun this:

```Shell
deactivate || true
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install poetry
poetry install --no-root --with test,docs -E "lexy_transformers"
pip install -e .
```
