#!/bin/sh
set -e

# Migrations run once per `up` in the separate "migrate" service
# (compose.yaml), not here.

# Nobody is connected yet: drop online counts left over from a crash.
python3 manage.py reset_presence

exec "$@"
