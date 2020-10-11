#!/bin/sh

set -e

project_dir='/app'

cd ${project_dir}

python -m alembic_script upgrade head  || true

gunicorn -c gunicorn.py src.app:app
