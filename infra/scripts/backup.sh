#!/bin/sh
# Dump the database and the avatars (called by `make backup [ENV=prod]`).
#
#   backups/db-<UTC time>.dump       pg_dump custom format (pg_restore)
#   backups/avatars-<UTC time>.tgz   the avatars folder
#
# Keeps the newest BACKUP_KEEP (default 7) of each. The backups stay on this
# machine: copy them somewhere else for real disaster recovery.
set -eu
cd "$(dirname "$0")/../.."
: "${COMPOSE:?run it through make backup}"

dir=${BACKUP_DIR:-backups}
keep=${BACKUP_KEEP:-7}
stamp=$(date -u +%Y%m%dT%H%M%SZ)
umask 077
mkdir -p "$dir"

# Write to a .part file first so a failed dump never looks like a backup,
# and remove it if anything fails.
trap 'rm -f "$dir"/*-"$stamp".*.part' EXIT
$COMPOSE exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' \
    > "$dir/db-$stamp.dump.part"
mv "$dir/db-$stamp.dump.part" "$dir/db-$stamp.dump"

# Through the running backend, or a one-off container when it is down
# (for example a deploy that failed halfway): same avatars volume.
if [ -n "$($COMPOSE ps -q --status running backend 2>/dev/null)" ]; then
    $COMPOSE exec -T backend tar czf - -C /backend/media/avatars .
else
    $COMPOSE run --rm -T --no-deps --entrypoint tar backend czf - -C /backend/media/avatars .
fi > "$dir/avatars-$stamp.tgz.part"
mv "$dir/avatars-$stamp.tgz.part" "$dir/avatars-$stamp.tgz"

prune() { # prune PATTERN: delete all but the newest $keep files
    # shellcheck disable=SC2012
    ls -1t "$dir"/$1 2>/dev/null | tail -n +$((keep + 1)) | while read -r old; do
        rm -f -- "$old"
    done
}
prune 'db-*.dump'
prune 'avatars-*.tgz'

echo "Backup written: $dir/db-$stamp.dump, $dir/avatars-$stamp.tgz"
