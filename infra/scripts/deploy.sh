#!/bin/sh
# Deploy one commit's images on the server, or roll back to an older one:
#
#   infra/scripts/deploy.sh <commit sha>      (or: make deploy SHA=<sha>)
#
# Run from the deploy folder (/srv/pong3d), which holds the compose files,
# the scripts and env/prod/ (no source code). The Deploy workflow uploads the
# files and runs this; it works by hand too.
#
# Steps:
#   1. back up (if the stack runs) and pull the app images for <sha>
#   2. run the migrations with the new image; on failure stop here, the
#      running version is untouched
#   3. `up`: recreate backend and nginx, wait until healthy; if the new
#      version does not get healthy, start the previous one again
#   4. record the sha in .env and deployed.log, drop old app images
#
# One backend only: `up` recreates it in place, so running games are
# dropped and the site is down for a few seconds. Rolling back does NOT
# undo migrations; see README "Deploys and rollback".
set -eu
cd "$(dirname "$0")/../.."

sha=${1:-}
case "$sha" in
    ""|*[!0-9a-f]*) echo "usage: $0 <commit sha (hex)>" >&2; exit 2 ;;
esac
[ "${#sha}" -ge 7 ] || { echo "the sha is too short" >&2; exit 2; }
[ -f env/prod/app.env ] || {
    echo "env/prod/ is missing: make env ENV=prod DOMAIN=... ACME_EMAIL=..." >&2
    exit 2
}

export PONG3D_ENV=prod
COMPOSE="docker compose -f compose.yaml -f compose.prod.yaml"
KEEP_IMAGES=${KEEP_IMAGES:-5}

get() { # get KEY: value from .env
    [ -f .env ] || return 0
    awk -v k="$1" 'index($0, k "=") == 1 { v = substr($0, length(k) + 2) } END { print v }' .env
}
set_var() { # set_var KEY VALUE in .env
    touch .env
    awk -v k="$1" -v v="$2" '
        BEGIN { done = 0 }
        index($0, k "=") == 1 { print k "=" v; done = 1; next }
        { print }
        END { if (!done) print k "=" v }
    ' .env > .env.tmp && mv .env.tmp .env
}

previous=$(get IMAGE_TAG)
echo "Deploying $sha (running now: ${previous:-nothing})"

if [ -n "$($COMPOSE ps -q db 2>/dev/null)" ]; then
    echo "Backup before deploy"
    COMPOSE="$COMPOSE" sh infra/scripts/backup.sh
fi

# Shell env wins over .env: use the new tag for this run only. .env is
# updated once the deploy is healthy, so a failed deploy leaves it pointing
# at the version to roll back to.
export IMAGE_TAG="$sha"
$COMPOSE pull migrate backend nginx

# Migrations before anything is replaced. They must work with the version
# that is still running (add first, remove one release later).
if ! $COMPOSE run --rm migrate; then
    echo "Migrations of $sha FAILED. Nothing was replaced; ${previous:-nothing} keeps running." >&2
    exit 1
fi

if ! $COMPOSE up -d --remove-orphans --wait --wait-timeout 300; then
    $COMPOSE ps -a
    $COMPOSE logs --tail=50 backend nginx || true
    echo "Deploy of $sha FAILED: it did not get healthy." >&2
    if [ -n "$previous" ]; then
        echo "Starting the previous version $previous again." >&2
        IMAGE_TAG="$previous" $COMPOSE up -d --remove-orphans --wait --wait-timeout 300 \
            && echo "Rolled back to $previous." >&2 \
            || echo "Rollback to $previous FAILED too: check make ps / make logs ENV=prod." >&2
    fi
    exit 1
fi

set_var IMAGE_TAG "$sha"
[ -n "${IMAGE_PREFIX:-}" ] && set_var IMAGE_PREFIX "$IMAGE_PREFIX"
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $sha" >> deployed.log
echo "Deployed $sha"

# Keep the newest $KEEP_IMAGES tags of each app image (for rollbacks).
prefix=${IMAGE_PREFIX:-$(get IMAGE_PREFIX)}
prefix=${prefix:-ghcr.io/bahbibe}
for repo in "$prefix/pong3d-backend" "$prefix/pong3d-nginx"; do
    docker images "$repo" --format '{{.Tag}}' | grep -v "^$sha\$" \
        | tail -n +"$KEEP_IMAGES" | while read -r tag; do
            docker rmi "$repo:$tag" >/dev/null 2>&1 || true
        done
done
docker image prune -f >/dev/null
