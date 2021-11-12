#!/bin/bash
set -e

# Apply database migrations
alembic --config=migrations/alembic.ini upgrade head

# Run API
gunicorn 'auth_api.app:create_app()' -w 2 --threads 2 -b 0.0.0.0:80
