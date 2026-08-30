#!/bin/sh
set -eu

python src/manage.py check --deploy
python src/manage.py migrate --noinput
python src/manage.py collectstatic --noinput

exec "$@"
