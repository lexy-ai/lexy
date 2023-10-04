# Lexy

Welcome to Lexy!
 
## Development

### Clone the repo

```Shell
git clone https://github.com/lexy-ai/lexy.git
```

### Install dependencies

Python 3.11 or greater is required. 

```Shell
# create a virtualenv
python3 -m venv venv 
source venv/bin/activate

# install poetry
pip install poetry

# install dev dependencies and extras
poetry install --no-root --with test,docs -E "lexy_transformers"

# install lexy in editable mode
pip install -e .

# initialize .env file
touch .env

# build docker images
docker-compose up --build -d
```

### What now?

Check whether everything boots via docker status checks. If not, try the following:

1. Uncomment code under `@app.on_event("startup")` in `main.py` (remember to comment it back after you're done).
2. Comment out `index_manager.create_index_models()` in `indexes.py`

The need for these manual operations result from the codebase evolving organically, without us having gotten around to implementing proper migrations. If you feel up for it, you should do so! 

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
