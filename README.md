# Lexy

Welcome to Lexy!
 
## Development

### Clone the repo

```Shell
git clone https://github.com/lexy-ai/lexy.git
```

### Install dependencies

Lexy requires Python 3.11 or greater. You can check your Python version by running `python3 --version`.

First create a virtual environment and install the dependencies.

```Shell
# Change to the lexy directory
cd lexy
# Create a virtualenv
python3 -m venv venv 
source venv/bin/activate
```

Then run the following to install the dev dependencies and build your docker containers.

```Shell
# Install dev dependencies
make install-dev
# Build docker containers
make build-dev
```

### Where to find services

| Service      | URL                        | Notes                                                         |
|--------------|----------------------------|---------------------------------------------------------------|
| Lexy API     | http://localhost:9900/docs | Swagger API docs                                              |
| Flower       | http://localhost:5556      | Celery task monitor                                           |
| RabbitMQ     | http://localhost:15672     | Username: `guest`, Password: `guest`                          |
| Postgres     | http://localhost:5432      | Database: `lexy`, Username: `postgres`, Password: `postgres`  |
| Project docs | http://localhost:8000      | Run `make serve-docs`<br/>Username: `lexy`, Password: `guest` |

### Configuring AWS

In order to upload and store files to Lexy, you'll need to configure AWS. You can use `aws configure` (recommended) or 
put `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` in your `.env` file.

You'll also need to specify an S3 bucket for file storage (for which your AWS credentials should have full access). 
You can do so by adding `DEFAULT_STORAGE_BUCKET=<name-of-your-S3-bucket>` to your `.env` file. Remember to rebuild your 
dev containers for the change to take effect (run `make rebuild-dev-containers` on the command line).

### Using OpenAI transformers

To use OpenAI embeddings in Lexy, you'll need to set the `OPENAI_API_KEY` environment variable. You can do so by adding 
the following to your `.env` file:

```Shell
OPENAI_API_KEY=<your-openai-api-key>
```

Do this before building your docker containers. Or, if you've already run `docker compose up`, you can run the 
following to rebuild the server and worker containers.

```shell
# Rebuild the server and worker containers
make rebuild-dev-containers
```

### Run the Dashboard

Lexy comes with a built-in dashboard to visualize pipelines. See [the dashboard README](./dashboard/README.md) for more details.

To start the dashboard, run:

```shell
cd dashboard
npm install
npm run dev
```

### PyCharm issues

If your virtualenv keeps getting bjorked by PyCharm, make sure that you're following the instructions above verbatim, 
and using `venv` instead of `.venv` for the path of your virtual environment.
