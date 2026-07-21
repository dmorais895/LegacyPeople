#!/bin/sh
set -e

# ---------------------------------------------------------------------------
# Security guard: SECRET_KEY is required in all environments.
# If it is missing the application should fail fast before exposing any port.
# ---------------------------------------------------------------------------
if [ -z "$SECRET_KEY" ]; then
  echo "ERROR: SECRET_KEY environment variable is not set."
  echo "       Set it in your .env file or pass it via the container runtime."
  exit 1
fi

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting application server..."
exec "$@"
