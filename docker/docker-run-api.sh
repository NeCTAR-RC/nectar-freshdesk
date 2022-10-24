#!/bin/sh
[ -f /vault/secrets/secret_envs ] && . /vault/secrets/secret_envs
export PATH="/venv/bin:$PATH"
gunicorn --bind 0.0.0.0:8613 --access-logfile=- --worker-tmp-dir /dev/shm --workers 2 nectar_freshdesk.wsgi:application
