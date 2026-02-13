#!/bin/sh

# Stopping if error occured
set -e

echo "Applying database migrations..."
flask db upgrade

echo "Starting Flask..."
exec python run.py
