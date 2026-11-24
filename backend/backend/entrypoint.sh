#!/bin/sh
set -e

# Apply the migrations that are in git. Never generate new ones here:
# they would only exist inside this container and drift between machines.
python3 manage.py migrate --noinput

# Nobody is connected yet: drop online counts left over from a crash.
python3 manage.py reset_presence

exec "$@"
