# pong3D

3D pong with remote games, tournaments, an AI opponent, chat and 42 login.
Django + Channels backend, vanilla JS frontend served by nginx.

## Quick start

Needs Docker with Compose v2 and GNU Make.

```bash
make env   # creates .env and env/dev/*.env with random secrets (keeps existing files)
make dev   # builds and starts everything, waits until it is healthy
```

Open https://localhost:1337 and accept the self-signed certificate.

`make dev` runs `make env` by itself when the env files are missing. For 42
login, set `INTRA_CLIENT_ID` and `INTRA_CLIENT_SECRET` in `env/dev/app.env`,
and register `https://localhost:1337/api/auth/intra/callback/` as the app's
redirect URI.

## Make targets

Add `ENV=prod` to act on the prod stack (default `ENV=dev`).

| Target | What it does |
| --- | --- |
| `make dev` | Dev stack: code bind-mounted, backend restarts on `.py` changes, nginx serves `./frontend` live |
| `make prod` | Prod stack: images only, ports 80/443, Let's Encrypt |
| `make down` | Stop and remove the containers, tools included (volumes are kept) |
| `make tools` | Grafana (127.0.0.1:3000), Prometheus, and in dev adminer (127.0.0.1:8080) and Prometheus on 127.0.0.1:9090 |
| `make tools-down` | Stop the tools only |
| `make restart s=backend` | Restart one service |
| `make logs [s=backend]` | Follow logs |
| `make ps` | List the containers and their health |
| `make migrate` | Apply migrations now (they also run on every `make dev`/`make prod`) |
| `make test` | Backend tests against a throwaway Postgres, cleaned up afterwards |
| `make env` | Create the env files (prod: `ENV=prod DOMAIN=... ACME_EMAIL=...`) |
| `make cert` | Prod: get the Let's Encrypt certificate (`STAGING=1` to try first) |
| `make backup` | Dump the database and the avatars to `backups/` (keeps 7) |
| `make restore FILE=... [AVATARS=...]` | Restore a backup (replaces the database content) |

## Layout

- `compose.yaml`: shared services (db, redis, migrate, backend, nginx; prometheus and grafana in the `tools` profile).
  `compose.dev.yaml` and `compose.prod.yaml` go on top; `compose.test.yaml` is for `make test`.
- `.env`: read by docker compose itself (ports, your uid). Not passed to containers.
- `env/dev/`, `env/prod/` (made by `make env`, not in git): one file per container.
  `app.env` (backend, migrate), `db.env`, `redis.env`, `grafana.env`, and `nginx.env` in prod.
  The templates are `env/*.example`.
- `backend/backend/`: Django project (`api`, `friends`, `chat`, `game`, `matchmaking`).
- `frontend/`: `index.html` and `static/` (served by nginx; three.js is vendored in `static/vendor`).
- `infra/nginx/`: nginx image and config (`common.conf` is shared by `dev.conf` and `prod.conf.template`).
- `infra/scripts/`: `gen-env.sh`, `backup.sh`, `restore.sh`. `infra/prometheus/`.

nginx serves everything on one origin: the frontend, `/api`, `/ws` and `/avatars`.
`/healthz`, `/metrics` and `/admin/` are not proxied. Startup is ordered by
healthchecks: db and redis, then the `migrate` job, then the backend
(`/healthz` checks the database and Redis), then nginx.

## Dev loop

- Frontend: edit files in `frontend/`, refresh the browser.
- Backend: save a `.py` file; watchfiles restarts daphne in a few seconds
  (`make logs s=backend`). Each restart drops running games, and the
  browser's status/notification sockets reconnect by themselves. If changes
  are not picked up (some Docker Desktop setups), add
  `WATCHFILES_FORCE_POLLING=1` to `env/dev/app.env` and run `make dev` again.
- The dev backend runs as your user (`HOST_UID`/`HOST_GID` in `.env`), so
  files it writes into the repo belong to you.
- New migration: `docker compose exec backend python manage.py makemigrations`,
  then `make migrate`.
- The Django port (`BACKEND_PORT` in `.env`, 8000 or the next free port) is
  on 127.0.0.1 for the seed script and `/admin`.

## Prod on a server

Any Linux box with Docker and ports 80/443 open, and a DNS name pointing at it.

```bash
make env ENV=prod DOMAIN=pong.example.org ACME_EMAIL=you@example.org
make prod                 # starts with a temporary self-signed certificate
make cert STAGING=1       # optional dry run against Let's Encrypt staging
make cert                 # real certificate; nginx reloads with it
```

- certbot renews in its own container; nginx reloads every 6 hours to pick
  up new certificates.
- Images run as a non-root user, with no bind mounts. Only 80 and 443 are
  published (`HTTP_PORT`/`HTTPS_PORT` in `.env` to change them).
- Each container only gets its own env file. Redis needs a password.
- Monitoring: `make tools ENV=prod`, then from your machine
  `ssh -L 3000:127.0.0.1:3000 <server>` and open http://localhost:3000
  (user admin, password `GF_SECURITY_ADMIN_PASSWORD` in `env/prod/grafana.env`).
  Prometheus has no host port in prod.
- 42 login: add `https://<DOMAIN>/api/auth/intra/callback/` to the intra app.
- Trying prod locally: `make env ENV=prod DOMAIN=localhost`, and if 80/443 are
  taken, `HTTP_PORT=8088 HTTPS_PORT=8443 make prod` (then set `API_URL`,
  `FRONTEND_URL` and `CSRF_TRUSTED_ORIGINS` in `env/prod/app.env` to
  `https://localhost:8443`). Local prod has its own database volume.

### Backups

`make backup ENV=prod` writes `backups/db-<time>.dump` and
`backups/avatars-<time>.tgz` and keeps the newest 7 (`BACKUP_KEEP`). Nightly
from cron:

```
0 3 * * * cd /srv/pong3d && make backup ENV=prod >> backups/backup.log 2>&1
```

`make restore ENV=prod FILE=backups/db-<time>.dump AVATARS=backups/avatars-<time>.tgz`
stops the backend, replaces the database content and unpacks the avatars
(files added after the backup stay). The backups are on the same machine:
copy them elsewhere for real disaster recovery.

## One backend replica only

Running games, bot games and the matchmaking queue live in the backend
process's memory. Never run more than one backend container
(no `--scale backend`). Restarting the backend drops the games in progress.

## Moving from older setups

- From the two-stack setup (`backend/docker-compose.yml` + `frontend/docker-compose.yml`):
  `make env` reads `backend/backend/.env`, so the existing `dbdata` volume
  (and your accounts) keep working. Remove the old containers once with
  `docker rm -f backend db nginx redis adminer prometheus grafana frontend`.
- From the single root `.env`: `make env` moves it to `.env.pre-split` and
  writes `env/dev/*.env` from its values. Delete `.env.pre-split` once
  `make dev` works.
- `frontend/node_modules` is no longer used and can be deleted.

## Tests by hand

```bash
docker run -d --rm --name pong3d-test-pg -p 127.0.0.1:55432:5432 \
  -e POSTGRES_USER=test -e POSTGRES_PASSWORD=test -e POSTGRES_DB=test postgres:16-alpine
cd backend/backend
DJANGO_SETTINGS_MODULE=ft_transcendence.test_settings python manage.py test
```
