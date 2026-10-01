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

# An explicit container command takes precedence over the default server choice.
if [ "$#" -eq 0 ]; then
  if [ "${DEBUG:-False}" = "True" ]; then
    set -- python manage.py runserver "0.0.0.0:${PORT:-8000}"
  else
    set -- gunicorn --bind "0.0.0.0:${PORT:-8000}" core.wsgi:application
  fi
fi

echo "Starting application command..."
exec "$@"
