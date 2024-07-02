#!/bin/bash
set -e

echo "Running start-worker.sh"

# Install extras if there's a requirements file in pipelines directory (e.g. /home/app/pipelines/requirements.txt)
EXTRA_REQUIREMENTS_FILE="/home/app/pipelines/${PIPELINE_EXTRAS_FILE:-requirements.txt}"
echo "Checking for extra requirements at $EXTRA_REQUIREMENTS_FILE"
if [ -f "$EXTRA_REQUIREMENTS_FILE" ] ; then
    echo "Installing extra requirements"
    pip install --no-input --disable-pip-version-check --log /var/log/lexy-pip.log -r "$EXTRA_REQUIREMENTS_FILE"
else
    echo "No extra requirements file found"
fi

# Celery worker options
celery_worker_queues=${CELERY_WORKER_QUEUES:-celery}
celery_worker_loglevel=${CELERY_WORKER_LOGLEVEL:-info}
celery_worker_options="-Q $celery_worker_queues --loglevel=$celery_worker_loglevel"

# Start worker
exec watchmedo auto-restart --directory /home/app/lexy/transformers/ --directory /home/app/pipelines/ --recursive --pattern '*.py' -- celery -A lexy.main.celery worker $celery_worker_options
