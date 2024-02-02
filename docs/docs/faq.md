# Frequently Asked Questions

## How do I add a new environment variable?

To add a new environment variable, add it to your `.env` file. If you don't have a `.env` file, you can simply create 
it by running `cp .env.example .env`. Then, open the `.env` file and add your new environment variable.

You should add environment variables **before** building your docker containers. Or, if you have already built your
containers, you can run the following to rebuild the server and worker containers. 

```bash
docker-compose up --build -d --no-deps lexyserver lexyworker
```

## Why is Lexy written in Python? Isn't Python too slow?

We chose Python because it is a language that is easy to read and write, is popular in the data and machine learning
communities, and is great for orchestration of complex systems. It's not yet clear what the biggest bottlenecks will be
in terms of performance, but we are confident that we can optimize performance using C/C++ bindings. And if that doesn't
work we'll just RIIR.

## I think the name Lexy is super cool!

We agree with you!
