#!/bin/sh
[ -f /vault/secrets/secret_envs ] && . /vault/secrets/secret_envs
export PATH="/venv/bin:$PATH"
nectar-freshdesk-agent
