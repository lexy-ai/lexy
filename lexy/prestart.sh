#!/bin/bash
set -e

echo "Running inside lexy/prestart.sh"

# Try to run `server_prestart.py` script for a maximum of 5 times
n=0
until [ "$n" -ge 5 ]
do
    echo "Running server_prestart.py to attempt reaching the database, attempt #$n"
    python /home/app/lexy/server_prestart.py && break
    n=$((n+1))
    sleep 3
done

# Create initial data in DB
python /home/app/lexy/seed_data.py
