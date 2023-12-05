# Installation

To run Lexy locally, you'll need [Docker](https://www.docker.com/get-started/) installed. You'll also need Python 3. We recommend Python 3.11 or greater.

## Clone the repo

```Shell
git clone https://github.com/lexy-ai/lexy.git
```


## Install dependencies

### Create a virtual env

```Shell
# create a virtualenv
python3 -m venv venv
source venv/bin/activate
```

### Install Python dependencies
```Shell
# install poetry
pip install poetry

# install dev dependencies and extras
poetry install --no-root --with test,docs -E "lexy_transformers"

# install lexy in editable mode
pip install -e .
pip install -e sdk-python
```

### Build docker images

```Shell
# initialize .env file if it doesn't exist
touch .env

# build docker images
docker-compose up --build -d
```

## Where to find services

The server will be running at http://localhost:9900. In addition, you can find the following services.


| Service      | URL                        | Notes                                                         |
|--------------|----------------------------|---------------------------------------------------------------|
| Lexy API     | http://localhost:9900/docs | Swagger API docs                                              |
| Flower       | http://localhost:5556      | Celery task monitor                                           |
| RabbitMQ     | http://localhost:15672     | Username: `guest`, Password: `guest`                          |
| Postgres     | http://localhost:5432      | Database: `lexy`, Username: `postgres`, Password: `postgres`  |
| Project docs | http://localhost:8000      | Run `make serve-docs`<br/>Username: `lexy`, Password: `guest` |


## Troubleshooting

### PyCharm issues

If your virtualenv keeps getting bjorked by PyCharm, make sure that you're following the instructions above verbatim, 
and using `venv` instead of `.venv` for the path of your virtual environment.
