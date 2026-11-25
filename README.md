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
| `make prod` | Prod stack built from source (local tries); a server uses `make deploy` |
| `make down` | Stop and remove the containers, tools included (volumes are kept) |
| `make tools` | Grafana (127.0.0.1:3000), Prometheus, and in dev adminer (127.0.0.1:8080) and Prometheus on 127.0.0.1:9090 |
| `make tools-down` | Stop the tools only |
| `make restart s=backend` | Restart one service |
| `make logs [s=backend]` | Follow logs |
| `make ps` | List the containers and their health |
| `make migrate` | Apply migrations now (they also run on every `make dev`/`make prod`) |
| `make test` | Backend tests against a throwaway Postgres, cleaned up afterwards |
| `make e2e [ARGS=...]` | Browser and websocket tests against the running stack (needs uv) |
| `make lock [ARGS=...]` | Update `backend/uv.lock` after changing `backend/pyproject.toml` (`LOCK_DIR=e2e`: `e2e/uv.lock`) |
| `make env` | Create the env files (prod: `ENV=prod DOMAIN=... ACME_EMAIL=...`) |
| `make cert` | Prod: get the Let's Encrypt certificate (`STAGING=1`: dry run, saves nothing) |
| `make backup` | Dump the database and the avatars to `backups/` (keeps 7) |
| `make restore FILE=... [AVATARS=...]` | Restore a backup (replaces the database content) |
| `make deploy SHA=...` | Server: deploy or roll back to a commit's images from GHCR |
| `make provision` | From your machine: provision the server with Ansible (`make provision-check` = dry run) |
| `make vault-new` / `make vault-edit` | Create / edit the encrypted Ansible vault with the prod secrets |

## Layout

- `compose.yaml`: shared services (db, redis, migrate, backend, nginx; prometheus and grafana in the `tools` profile).
  `compose.dev.yaml` and `compose.prod.yaml` go on top; `compose.test.yaml` is for `make test`.
- `.env`: read by docker compose itself (ports, your uid). Not passed to containers.
- `env/dev/`, `env/prod/` (made by `make env`, not in git): one file per container.
  `app.env` (backend, migrate), `db.env`, `redis.env`, `grafana.env`, and `nginx.env` in prod.
  The templates are `env/*.example`.
- `backend/`: Django project.
  - `config/`: settings, URLs, ASGI app, websocket routes, `/healthz`.
  - `apps/`: `accounts` (users, auth, 2FA), `notifications` (stored and live, `notify()`),
    `presence` (online status, in Redis), `friends`, `chat`, `game`, `matchmaking`.
    The app labels are the old ones (`accounts` is still `api` in the database and migrations).
  - `core/`: shared helpers (JSON responses, Redis URL).
  - `media/avatars/`: uploaded avatars (a named volume in prod). Only the default one is in git.
- `e2e/`: browser (Playwright) and websocket tests, run against a running stack.
- `docs/`: server setup (`bootstrap-vps.md`), the subject's module checklist, a Postman collection of the API.
- `frontend/`: the single-page app, no framework and no build step (see Frontend below).
  `index.html` is the shell; `static/` is served by nginx (three.js is vendored in `static/vendor`).
- `infra/nginx/`: nginx image and config (`common.conf` is shared by `dev.conf` and `prod.conf.template`).
- `infra/scripts/`: `gen-env.sh`, `backup.sh`, `restore.sh`, `deploy.sh`. `infra/prometheus/`.
- `infra/ansible/`: server provisioning (Docker, deploy user, ssh, ufw, env files from the vault, backups cron, certificate).
- `.github/workflows/`: `ci.yml` (tests with coverage, lint, deploy checks, images to GHCR), `deploy.yml` (deploy over SSH).

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
  on 127.0.0.1 for `/admin`.
- Demo accounts: `docker compose exec backend python manage.py create_demo_users`
  (dev only: refuses to run when `DJANGO_ALLOWED_HOSTS` has a public name).

## Frontend

Vanilla JavaScript modules, loaded as they are by the browser: custom
elements in the light DOM (Bootstrap and `static/css` apply), the History
API for routing. `frontend/static/js/`:

- `main.js`: entry point. Starts the router; links with `data-link` change
  the page without a reload (ctrl/middle click still opens a new tab).
- `core/`: the small framework.
  - `router.js`: the route table (path, element tag, access, title) and the
    guards: logged out, 2FA code pending, profile not set up.
  - `session.js`: the current user, loaded from `/api/auth/me/` once per
    page load and asked again only when the guard would redirect.
  - `page.js`: `Component` and `Page`, the base of every element (below).
  - `html.js`: the `html` template tag and `render()`.
  - `api.js`: the only `fetch()`. Every call resolves to
    `{ok, status, data, message, errors}`; `toastOnError(result)` shows a
    failure. A 401 sends you to `/login`.
  - `store.js`: observable values: unread notifications, online users.
  - `sockets.js` (reconnecting WebSocket), `toast.js`, `overlay.js`,
    `escape.js`, `config.js`.
- `services/`: what runs while you are logged in: `presence.js` and
  `notifications.js` (sockets that fill the stores), `game.js` (invite,
  play again).
- `components/`: elements used inside pages (nav, notifications menu,
  search bar, chat contacts and conversation, history rows).
- `pages/`: one module per page.

**A page** extends `Page` and renders in `mount()`:

```js
import { toastOnError } from "../core/api.js";
import { html, render } from "../core/html.js";
import { Page } from "../core/page.js";

class FriendsPage extends Page {
  async mount() {
    this.render(html`<main-nav></main-nav><ul class="friends"></ul>`);
    const result = await this.api.get("/api/friends/");
    if (!toastOnError(result)) return;
    render(this.querySelector(".friends"), html`${result.data.map((f) => html`<li>${f.friend.username}</li>`)}`);
  }
}
customElements.define("friends-page", FriendsPage);
```

Then import the module in `pages/index.js` and add a route in
`core/router.js` (`{ path: "/friends", tag: "friends-page", access: "user", title: "Friends" }`).
URL parameters are `this.params` (`/friend/:uuid` gives `this.params.uuid`),
the query string is `this.query`.

Rules the code follows:

- **Markup only through `html`.** It escapes every value put in it, so
  usernames, messages and other server data can never become markup.
  Nested `html` templates and arrays of them are inserted as they are;
  `raw()` is for trusted static markup only. `render()` refuses plain
  strings. No `innerHTML` anywhere else.
- **Set things up through the base class**: `this.on(target, type, fn)`,
  `this.api`, `this.socket(path, handlers)`, `this.timeout(fn, ms)`,
  `this.subscribe(store, fn)`. All of them stop when the element leaves the
  page: listeners are removed, requests in flight are cancelled (their
  result is `{aborted: true}`), sockets close, timers clear.
- **No global state** on `window`: the session and the stores hold it.

There is no bundler: a new module is one more file. The Content-Security-Policy
(`infra/nginx/common.conf`) only allows scripts from the site itself, the
pinned Bootstrap bundle and the import map in `index.html` by hash: if you
change the import map, update its sha256 there. Our JS and CSS are served
with `Cache-Control: no-cache` (revalidated on every load), so a deploy never
mixes old and new modules.

## Prod on a server

Setup: [docs/bootstrap-vps.md](docs/bootstrap-vps.md). In short, from your
machine:

```bash
cp infra/ansible/inventory/prod.yml.example infra/ansible/inventory/prod.yml   # fill in
make vault-new        # encrypted prod secrets (committed; long vault password)
make provision        # Docker, deploy user, ssh, ufw, swap, /srv/pong3d, env files, backup cron
# GitHub: production environment secrets + DEPLOY_ENABLED=true, then run the Deploy workflow
make provision        # again after the first deploy: gets the Let's Encrypt certificate
```

The server holds only the compose files, the scripts and `env/prod/`; it runs
the images CI built. On the server itself, `make deploy SHA=<commit>`,
`make cert`, `make backup ENV=prod` and `make logs ENV=prod` work in
`/srv/pong3d`.

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

### Deploys and rollback

- Every push to main runs CI: tests, `manage.py check --deploy`, then
  `ghcr.io/bahbibe/pong3d-backend` and `pong3d-nginx` are pushed, tagged with
  the commit sha (and `main`). The Deploy workflow then runs
  `infra/scripts/deploy.sh <sha>` on the server over SSH (only when the
  repository variable `DEPLOY_ENABLED` is `true`).
- `deploy.sh`: backup, pull, migrations with the new image (if they fail,
  nothing is replaced), then `up` and wait until healthy. If the new version
  does not get healthy, it starts the previous one again and fails.
  `deployed.log` lists what was deployed when.
- Roll back by hand: Actions > Deploy > Run workflow with an older sha of
  main (`gh workflow run deploy.yml -f sha=<sha>`), or `make deploy SHA=<sha>`
  on the server. The images are still in GHCR; nothing is rebuilt. The
  server keeps the last 5 versions locally.
- **A rollback does not undo migrations.** Keep migrations working with the
  previous release: add a column in one release, use it, drop the old one a
  release later. If a migration has to be undone, restore the backup taken
  right before that deploy (`make restore ENV=prod FILE=...`).
  Moving a model to another app works the same way: state-only migrations,
  the table keeps its name (see `apps/notifications/migrations/0001_initial.py`).
  An older image run against it re-creates the old content type row;
  `docker compose exec backend python manage.py remove_stale_contenttypes`
  removes it, but it does no harm.
- One backend replica: each deploy recreates it, so the site is down for a
  few seconds and running games are dropped. No blue/green on purpose (two
  backends cannot share game state).

### Backups

`make backup ENV=prod` writes `backups/db-<time>.dump` and
`backups/avatars-<time>.tgz` and keeps the newest 7 (`BACKUP_KEEP`). The
Ansible `app` role installs it nightly in the deploy user's crontab:

```
0 3 * * * cd /srv/pong3d && BACKUP_KEEP=7 make backup ENV=prod >> backups/backup.log 2>&1
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

- The Django project moved from `backend/backend/` to `backend/`, and
  uploaded avatars from `backend/backend/avatars/` to `backend/media/avatars/`.
  Move your local uploads there if they are still in the old place. An old
  `backend/backend/.env` is no longer read: `env/dev/` holds its values.
- From the single root `.env`: `make env` moves it to `.env.pre-split` and
  writes `env/dev/*.env` from its values. Delete `.env.pre-split` once
  `make dev` works.
- `frontend/node_modules` is no longer used and can be deleted.

## Tests by hand

```bash
docker run -d --rm --name pong3d-test-pg -p 127.0.0.1:55432:5432 \
  -e POSTGRES_USER=test -e POSTGRES_PASSWORD=test -e POSTGRES_DB=test postgres:16-alpine
cd backend
uv sync     # .venv with the locked dependencies, dev group included
DJANGO_SETTINGS_MODULE=config.test_settings uv run python manage.py test
```

Coverage, as in CI: `uv sync --group test`, then
`DJANGO_SETTINGS_MODULE=config.test_settings uv run coverage run manage.py test`
and `uv run coverage report` (fails below `fail_under` in `pyproject.toml`).

## E2E tests

`e2e/` drives the real stack: every page in Chromium, register/login/setup,
settings and avatar upload, 2FA, notifications and presence, chat between two
browsers, matchmaking and games, socket reconnects after a backend restart.

```bash
make dev
make e2e                          # all of them (installs Chromium the first time)
make e2e ARGS="-k chat -x"        # pytest arguments
make e2e ARGS="--headed --slowmo 300"   # watch it
```

It needs uv on your machine. The tests create throwaway accounts in the dev
database, read 2FA secrets from it and restart the backend once (through
`docker compose`). Another stack: `E2E_BASE_URL=https://localhost:8443 make e2e ENV=prod`.
Failed tests leave screenshots and traces in `e2e/test-results/`
(`uv run playwright show-trace <file>`). CI runs them against the dev stack
before building images.

## Lint

Ruff for Python (settings in `backend/pyproject.toml`), ESLint and Prettier
for the frontend (`frontend/eslint.config.js`, `frontend/.prettierrc.json`) and
a few file checks run through pre-commit. pre-commit installs Node and the JS
tools itself: there is no package.json. CI runs the same hooks on every file.

```bash
uvx pre-commit install           # once: runs the hooks on each commit
uvx pre-commit run --all-files   # by hand
```

`.git-blame-ignore-revs` lists the formatting-only commits; run
`git config blame.ignoreRevsFile .git-blame-ignore-revs` once so `git blame`
skips them.

## Dependencies

`backend/pyproject.toml` lists the direct dependencies. `backend/uv.lock`
pins every package, with hashes. The images and CI install exactly the
lock (`uv sync --frozen` / `--locked`), and CI runs `pip-audit` on it
before building images.

- Add or change a dependency: edit `pyproject.toml`, then `make lock`.
- Upgrade one package: `make lock ARGS="--upgrade-package django"`.
- Upgrade everything within the ranges: `make lock ARGS=--upgrade`.

Dependabot (`.github/dependabot.yml`) opens grouped update PRs once a
month for uv, the Dockerfiles, the compose images, the Actions and the
pre-commit hooks. Postgres majors and Python minors are skipped (they need
a migration of their own).

Commit `uv.lock` together with the change. `make lock` runs uv 0.11.32 in
a container. To move to a newer uv, change that version in the Makefile,
`backend/Dockerfile` and `.github/workflows/ci.yml` together.
