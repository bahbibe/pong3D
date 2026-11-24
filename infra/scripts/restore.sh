#!/bin/sh
# Restore a backup made by backup.sh (called by `make restore`):
#
#   make restore FILE=backups/db-<time>.dump [AVATARS=backups/avatars-<time>.tgz] [ENV=prod]
#
# REPLACES the current database content (pg_restore --clean). The backend is
# stopped meanwhile, so running games are dropped.
set -eu
cd "$(dirname "$0")/../.."
: "${COMPOSE:?run it through make restore}"
: "${FILE:?FILE=backups/db-<time>.dump is required}"
AVATARS=${AVATARS:-}

[ -f "$FILE" ] || { echo "No such file: $FILE" >&2; exit 2; }
[ -z "$AVATARS" ] || [ -f "$AVATARS" ] || { echo "No such file: $AVATARS" >&2; exit 2; }

$COMPOSE stop backend
# Start the backend again whatever happens below.
trap '$COMPOSE start backend >/dev/null' EXIT

$COMPOSE exec -T db sh -c \
    'pg_restore --clean --if-exists --no-owner -U "$POSTGRES_USER" -d "$POSTGRES_DB"' \
    < "$FILE"
echo "Database restored from $FILE"

if [ -n "$AVATARS" ]; then
    # The backend is stopped: unpack through a one-off container.
    $COMPOSE run --rm -T --no-deps --entrypoint tar backend xzf - -C /backend/media/avatars \
        < "$AVATARS"
    echo "Avatars restored from $AVATARS"
fi
