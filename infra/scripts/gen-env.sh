#!/bin/sh
# Create the env files (called by `make env`).
#
#   make env                                   dev:  env/dev/*.env
#   make env ENV=prod DOMAIN=example.org ACME_EMAIL=you@example.org
#                                              prod: env/prod/*.env
#
# - .env (repo root): variables docker compose reads (ports, your uid).
# - env/<ENV>/app.env, db.env, redis.env, grafana.env (+ nginx.env in prod):
#   one file per container, so each one only sees its own secrets.
#
# Existing files are never overwritten. Passwords shared by two files (the
# Postgres and Redis ones) are written to both. Dev reuses the values of the
# old single .env (or backend/backend/.env): the existing dbdata volume was
# created with that Postgres password.
set -eu
cd "$(dirname "$0")/../.."

ENV=${ENV:-dev}
DOMAIN=${DOMAIN:-}
ACME_EMAIL=${ACME_EMAIL:-}
case "$ENV" in dev|prod) ;; *) echo "ENV must be dev or prod" >&2; exit 2 ;; esac

umask 077

# get FILE KEY: value of KEY in FILE (empty if the file or key is missing).
get() {
    [ -f "$1" ] || return 0
    awk -v k="$2" 'index($0, k "=") == 1 { v = substr($0, length(k) + 2) } END { print v }' "$1"
}

# set_var FILE KEY VALUE: replace KEY=... in FILE, or append it.
set_var() {
    awk -v k="$2" -v v="$3" '
        BEGIN { done = 0 }
        index($0, k "=") == 1 { print k "=" v; done = 1; next }
        { print }
        END { if (!done) print k "=" v }
    ' "$1" > "$1.tmp" && mv "$1.tmp" "$1"
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

# --- 1. Root .env (compose variables) ----------------------------------------
# Before the split, .env held every app setting. Keep it as .env.pre-split
# (the app values are read from it below) and start a compose-only .env.
if [ -f .env ] && grep -q '^DJANGO_SECRET_KEY=' .env; then
    mv .env .env.pre-split
    echo "Moved the old single .env to .env.pre-split (its values are reused)."
fi
if [ ! -f .env ]; then
    cp .env.example .env
    old_port=$(get .env.pre-split BACKEND_PORT)
    port=${old_port:-8000}
    if [ -z "$old_port" ]; then
        while port_in_use "$port" && [ "$port" -lt 8100 ]; do port=$((port + 1)); done
    fi
    set_var .env BACKEND_PORT "$port"
    set_var .env HOST_UID "$(id -u)"
    set_var .env HOST_GID "$(id -g)"
    echo "Created .env (BACKEND_PORT=$port)."
fi

# --- 2. Container env files ----------------------------------------------------
dir=env/$ENV
if [ -f "$dir/app.env" ]; then
    echo "$dir/app.env already exists, keeping $dir."
    exit 0
fi

if [ "$ENV" = prod ] && [ -z "$DOMAIN" ]; then
    echo "Prod needs a domain: make env ENV=prod DOMAIN=example.org ACME_EMAIL=you@example.org" >&2
    echo "(DOMAIN=localhost to try prod on this machine.)" >&2
    exit 2
fi

# Old values to carry over (dev only: prod starts with fresh secrets).
old=""
if [ "$ENV" = dev ]; then
    if [ -f .env.pre-split ]; then old=.env.pre-split
    elif [ -f backend/backend/.env ]; then old=backend/backend/.env
    fi
fi

mkdir -p "$dir"

pick() { # pick KEY DEFAULT: existing env file, then old file, then DEFAULT
    v=$(get "$dir/db.env" "$1"); [ -n "$v" ] || v=$(get "$dir/redis.env" "$1")
    [ -n "$v" ] || { [ -n "$old" ] && v=$(get "$old" "$1"); } || true
    [ -n "$v" ] && printf '%s' "$v" || printf '%s' "$2"
}

pg_user=$(pick POSTGRES_USER pong3d)
pg_db=$(pick POSTGRES_DB pong3d)
pg_password=$(pick POSTGRES_PASSWORD "$(random_hex)")
redis_password=$(pick REDIS_PASSWORD "$(random_hex)")

# app.env: template, then old values for the keys it has, then the rest.
cp env/app.env.example "$dir/app.env.new"
if [ -n "$old" ]; then
    for key in $(grep -o '^[A-Z_]*=' env/app.env.example | tr -d '='); do
        value=$(get "$old" "$key")
        [ -n "$value" ] && set_var "$dir/app.env.new" "$key" "$value"
    done
fi
[ -n "$(get "$dir/app.env.new" DJANGO_SECRET_KEY)" ] || set_var "$dir/app.env.new" DJANGO_SECRET_KEY "$(random_hex)"
[ -n "$(get "$dir/app.env.new" JWT_SECRET)" ] || set_var "$dir/app.env.new" JWT_SECRET "$(random_hex)"
set_var "$dir/app.env.new" POSTGRES_USER "$pg_user"
set_var "$dir/app.env.new" POSTGRES_PASSWORD "$pg_password"
set_var "$dir/app.env.new" POSTGRES_DB "$pg_db"
set_var "$dir/app.env.new" REDIS_URL "redis://:$redis_password@redis:6379/0"

if [ "$ENV" = prod ]; then
    set_var "$dir/app.env.new" DJANGO_DEBUG 0
    # 127.0.0.1: container healthcheck. backend: prometheus scrapes backend:8000.
    set_var "$dir/app.env.new" DJANGO_ALLOWED_HOSTS "$DOMAIN,127.0.0.1,backend"
    set_var "$dir/app.env.new" CSRF_TRUSTED_ORIGINS "https://$DOMAIN"
    set_var "$dir/app.env.new" API_URL "https://$DOMAIN"
    set_var "$dir/app.env.new" FRONTEND_URL "https://$DOMAIN/"
    if [ "$DOMAIN" = localhost ]; then hsts=0; else hsts=31536000; fi
    set_var "$dir/app.env.new" DJANGO_HSTS_SECONDS "$hsts"

    cp env/nginx.env.example "$dir/nginx.env"
    set_var "$dir/nginx.env" DOMAIN "$DOMAIN"
    set_var "$dir/nginx.env" ACME_EMAIL "$ACME_EMAIL"
    set_var "$dir/nginx.env" HSTS_MAX_AGE "$hsts"
fi
mv "$dir/app.env.new" "$dir/app.env"

if [ ! -f "$dir/db.env" ]; then
    cp env/db.env.example "$dir/db.env"
    set_var "$dir/db.env" POSTGRES_USER "$pg_user"
    set_var "$dir/db.env" POSTGRES_PASSWORD "$pg_password"
    set_var "$dir/db.env" POSTGRES_DB "$pg_db"
fi
if [ ! -f "$dir/redis.env" ]; then
    cp env/redis.env.example "$dir/redis.env"
    set_var "$dir/redis.env" REDIS_PASSWORD "$redis_password"
fi
if [ ! -f "$dir/grafana.env" ]; then
    cp env/grafana.env.example "$dir/grafana.env"
    set_var "$dir/grafana.env" GF_SECURITY_ADMIN_PASSWORD "$(random_hex)"
fi

echo "Created $dir/ (app.env, db.env, redis.env, grafana.env$([ "$ENV" = prod ] && echo ', nginx.env'))."
[ -n "$old" ] && echo "Values carried over from $old."
[ -n "$(get "$dir/app.env" INTRA_CLIENT_ID)" ] || echo "Set INTRA_CLIENT_ID/SECRET in $dir/app.env for 42 login."
exit 0
