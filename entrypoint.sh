#!/bin/sh

# Stop if error occurs
set -e

export DATABASE_URL

echo "Extracting database config..."
DB_HOST=$(python -c "import os, urllib.parse; print(urllib.parse.urlparse(os.environ['DATABASE_URL']).hostname)")
DB_PORT=$(python -c "import os, urllib.parse; print(urllib.parse.urlparse(os.environ['DATABASE_URL']).port)")

echo "Applying database migrations..."

until nc -z -v -w 30 "$DB_HOST" "$DB_PORT"; do
  echo "Waiting for database connection..."
  sleep 1
done

flask db upgrade

echo "Starting Flask..."
exec gunicorn --workers 5 --bind 0.0.0.0:5000 run:app
