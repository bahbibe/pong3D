# pong3D

3D pong with remote games, tournaments, an AI opponent, chat and 42 login.
Django + Channels backend, vanilla JS frontend served by nginx.

## Quick start

Needs Docker with Compose v2 and GNU Make.

```bash
make env   # creates .env with random secrets (keeps an existing one)
make dev   # builds and starts everything
```

Open https://localhost:1337 and accept the self-signed certificate.

`make dev` runs `make env` by itself when `.env` is missing. For 42 login,
set `INTRA_CLIENT_ID` and `INTRA_CLIENT_SECRET` in `.env`, and register
`https://localhost:1337/api/auth/intra/callback/` as the app's redirect URI.

## Make targets

| Target | What it does |
| --- | --- |
| `make dev` | Dev stack: code bind-mounted, backend restarts on `.py` changes, nginx serves `./frontend` live |
| `make prod` | Prod-like stack: images only, avatars in a named volume |
| `make down` | Stop and remove the containers, tools included (volumes are kept) |
| `make tools` | Start adminer (8080), grafana (3000), prometheus (9090) on 127.0.0.1 |
| `make tools-down` | Stop the tools only |
| `make restart s=backend` | Restart one service |
| `make logs [s=backend]` | Follow logs |
| `make ps` | List the containers |
| `make test` | Backend tests against a throwaway Postgres, cleaned up afterwards |
| `make env` | Create `.env` |

## Layout

- `compose.yaml`: shared services (db, redis, backend, nginx; adminer, prometheus and grafana in the `tools` profile).
  `compose.dev.yaml` and `compose.prod.yaml` go on top; `compose.test.yaml` is for `make test`.
- `backend/backend/`: Django project (`api`, `friends`, `chat`, `game`, `matchmaking`).
- `frontend/`: `index.html` and `static/` (served by nginx; three.js is vendored in `static/vendor`).
- `infra/nginx/`: nginx image and config (TLS on 1337, CSP, `/api` and `/ws` proxy).
- `infra/prometheus/`, `infra/scripts/`.

nginx serves everything on one origin: the frontend, `/api`, `/ws` and `/avatars`.
The tools (`make tools`) and the Django port (`BACKEND_PORT`, 8000 or the
next free port) are bound to 127.0.0.1 only. Grafana's first login is admin/admin.

## Dev loop

- Frontend: edit files in `frontend/`, refresh the browser.
- Backend: save a `.py` file; watchfiles restarts daphne in a few seconds
  (`make logs s=backend`). Each restart drops running games, and the
  browser's status/notification sockets reconnect by themselves. If changes
  are not picked up (some Docker Desktop setups), add
  `WATCHFILES_FORCE_POLLING=1` to `.env` and run `make dev` again.
- New migration: `docker compose exec backend python manage.py makemigrations`,
  then `make restart s=backend` (migrations run when the container starts).

## One backend replica only

Running games, bot games and the matchmaking queue live in the backend
process's memory. Never run more than one backend container
(no `--scale backend`). Restarting the backend drops the games in progress.

## Moving from the old two-stack setup

The old `backend/docker-compose.yml` and `frontend/docker-compose.yml` are gone.
`make env` copies `backend/backend/.env` to `.env`, so the existing `dbdata`
volume (and your accounts) keep working. Remove the old containers once with
`docker rm -f backend db nginx redis adminer prometheus grafana frontend`
if they still exist. `frontend/node_modules` is no longer used and can be deleted.

## Tests by hand

```bash
docker run -d --rm --name pong3d-test-pg -p 127.0.0.1:55432:5432 \
  -e POSTGRES_USER=test -e POSTGRES_PASSWORD=test -e POSTGRES_DB=test postgres:16-alpine
cd backend/backend
DJANGO_SETTINGS_MODULE=ft_transcendence.test_settings python manage.py test
```
