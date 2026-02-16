#!/bin/sh

# Stopping if error occured
set -e

echo "Applying database migrations..."
# adding wait for the database to be ready
until nc -z -v -w30 $DB_HOST $DB_PORT; do
  echo "Waiting for database connection..."
  sleep 1
done
flask db upgrade

echo "Starting Flask..."
exec python run.py
