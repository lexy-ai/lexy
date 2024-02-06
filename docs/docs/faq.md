# Frequently Asked Questions

## How do I add a new environment variable?

To add a new environment variable, add it to your `.env` file. If you don't have a `.env` file, you can simply create 
it by copying the file `.env.example`. 

```bash
cp -n .env.example .env
```

Then open the `.env` file and add your new environment variable.

```shell title=".env" hl_lines="4"
# Example .env file
OPENAI_API_KEY=<secret_api_key>
S3_BUCKET=<s3_bucket_name>
NEW_ENV_VAR=<new_env_var_value>
```


You should add environment variables **before** building your docker containers. Or if you have already built your
containers, you can run the following to rebuild the server and worker containers. 

```bash
docker-compose up --build -d --no-deps lexyserver lexyworker
```

Verify that your new environment variable has been added to the server and worker containers.

```bash
docker exec lexy-server env | grep -i NEW_ENV_VAR
docker exec lexy-celeryworker env | grep -i NEW_ENV_VAR
```

## Why is Lexy written in Python? Isn't Python slow?

Python is (1) easy to read and write, (2) extremely popular in the data and machine learning communities, and (3) great 
for orchestration of complex systems. It's not yet clear to us what the biggest bottlenecks will be, but we 
are confident that we can optimize performance using C/C++ bindings. And if that doesn't work, we'll just RIIR.

## I think the name Lexy is super cool.

We agree with you! The name comes from "lexicon," defined as the vocabulary of a person, language, or branch of
knowledge.
