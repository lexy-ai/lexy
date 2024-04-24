#!/bin/bash
set -e

echo "Running start-server.sh"

# If there's a prestart.sh script in the lexy directory or other path specified, run it before starting
PRE_START_PATH=${PRE_START_PATH:-/home/app/lexy/prestart.sh}
echo "Checking for script in $PRE_START_PATH"
if [ -f "$PRE_START_PATH" ] ; then
    echo "Running script $PRE_START_PATH"
    . "$PRE_START_PATH"
else
    echo "There is no script $PRE_START_PATH"
fi

reload_options="--reload-dir /home/app/lexy --reload-dir /home/app/pipelines"

# Start server
exec poetry run uvicorn lexy.main:app --host 0.0.0.0 --port 9900 --reload $reload_options
