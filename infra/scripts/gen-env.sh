#!/bin/sh
# Create ./.env for docker compose (called by `make env`).
#
# - .env exists: keep it.
# - backend/backend/.env exists (old layout): copy it. It holds the password
#   the existing dbdata volume was created with; new random secrets would
#   lock you out of your own database.
# - otherwise: start from .env.example with random secrets.
#
# Then add BACKEND_PORT (host port of the Django dev server) if missing,
# using 8000 or the next free port.
set -eu
cd "$(dirname "$0")/../.."

if [ -f .env ]; then
    echo ".env already exists, keeping it."
    exit 0
fi

# set_var KEY VALUE: replace KEY=... in .env, or append it.
set_var() {
    awk -v k="$1" -v v="$2" '
        BEGIN { done = 0 }
        index($0, k "=") == 1 { print k "=" v; done = 1; next }
        { print }
        END { if (!done) print k "=" v }
    ' .env > .env.tmp && mv .env.tmp .env
}

random_hex() {
    if command -v openssl >/dev/null 2>&1; then
        openssl rand -hex 32
    else
        od -An -N32 -tx1 /dev/urandom | tr -d ' \n'
    fi
}

port_in_use() {
    if command -v ss >/dev/null 2>&1; then
        ss -ltn | awk '{print $4}' | grep -Eq "[:.]$1\$"
    elif command -v lsof >/dev/null 2>&1; then
        lsof -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1
    else
        return 1
    fi
}

umask 077
if [ -f backend/backend/.env ]; then
    cp backend/backend/.env .env
    echo "Copied backend/backend/.env to .env (keeps your database password)."
else
    cp .env.example .env
    set_var DJANGO_SECRET_KEY "$(random_hex)"
    set_var JWT_SECRET "$(random_hex)"
    set_var POSTGRES_PASSWORD "$(random_hex)"
    set_var POSTGRES_USER pong3d
    set_var POSTGRES_DB pong3d
    echo "Created .env with random secrets. Add INTRA_CLIENT_ID/SECRET for 42 login."
fi

if ! grep -q '^BACKEND_PORT=' .env; then
    port=8000
    while port_in_use "$port" && [ "$port" -lt 8100 ]; do
        port=$((port + 1))
    done
    printf '\n# Host port of the Django dev server (seed script, /admin).\nBACKEND_PORT=%s\n' "$port" >> .env
    echo "BACKEND_PORT=$port"
fi
