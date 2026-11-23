# Phase 1: Infra and config

Scope: `backend/docker-compose.yml`, `frontend/docker-compose.yml`, Dockerfiles, `backend/backend/entrypoint.sh`, `backend/nginx/*`, `backend/prometheus/prometheus.yml`, `settings.py`, `asgi.py`, `urls.py`, `requirements.txt`, ignore files.

| Location | Severity | Problem | Fix |
|---|---|---|---|
| `backend/backend/ft_transcendence/asgi.py:16` + `settings.py:19` | critical | `AllowedHostsOriginValidator` checks Origin against `ALLOWED_HOSTS = ["*"]`, so any site is allowed. WS auth uses the `access_token` cookie, so a malicious page can open `/ws/chat/...`, `/ws/game/...` as the victim (cross-site WebSocket hijacking). | Set real `ALLOWED_HOSTS` (e.g. `localhost`, the deploy host). Keep the validator. |
| `settings.py:55-57` | critical | `CORS_ALLOW_ALL_ORIGINS = True` with `CORS_ALLOW_CREDENTIALS = True`. django-cors-headers reflects any Origin, so any site can make credentialed API calls and read responses (cookie JWT). | Use `CORS_ALLOWED_ORIGINS = [frontend origin]` from env. |
| `settings.py:14` | high | Hardcoded `SECRET_KEY` committed to git. | `SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]`, add to `.env.example`, rotate. |
| `settings.py:17` | high | `DEBUG = True` hardcoded. Leaks settings, SQL and stack traces on any error page. | `DEBUG = os.getenv("DJANGO_DEBUG") == "1"`. |
| `backend/backend/` (build context) | high | `backend/.dockerignore` sits one level above the build context (`build: ./backend`), so it is not used. `COPY . .` bakes `backend/backend/.env` (JWT secret, intra client secret, DB password) into the image. | Move/add `.dockerignore` in `backend/backend/` with `.env`, `__pycache__`, `avatars/*`. |
| `backend/docker-compose.yml` | high | Host ports published: backend `8000` (plain HTTP, skips nginx TLS), adminer `8080` (DB UI), grafana `3000` (default admin/admin), prometheus `9090`. | Publish only nginx. Bind tooling to `127.0.0.1:` if needed. Set `GF_SECURITY_ADMIN_PASSWORD`. |
| `backend/backend/ft_transcendence/urls.py:21` | med | `django_prometheus.urls` mounted at `/` exposes `/metrics` publicly through port 8000. `admin/` also exposed. | Do not proxy `/metrics` in nginx; block on public port. |
| `backend/docker-compose.yml` | med | `env_file: ./backend/.env` given to `redis`, `adminer` and `db`. Every container gets `JWT_SECRET` and `INTRA_CLIENT_SECRET`. | Split env files per service, or use `environment:` with only needed vars. |
| `backend/backend/entrypoint.sh:3` | high | Runs `makemigrations` at boot. With the bind mount it writes new migration files into the repo from the container, and different machines can generate conflicting migrations. | Only `migrate` at boot. Generate migrations in dev and commit them. |
| `backend/backend/Dockerfile:18` | med | `CMD runserver` (dev server, autoreload). Autoreload restarts the process on file change and kills in-memory games (`game_manager.py`). Daphne line is commented. | Use `daphne -b 0.0.0.0 -p 8000 ft_transcendence.asgi:application`. |
| `backend/backend/ft_transcendence/asgi.py:5-13` | med | `chat.middleware` imports `django.contrib.auth.models.User` before `get_asgi_application()`. Works under runserver (Django already set up), crashes with `AppRegistryNotReady` under plain daphne. Blocks the fix above. | Call `django_asgi_application = get_asgi_application()` right after `setdefault`, before other imports. |
| `backend/docker-compose.yml` | med | `depends_on: db` with no healthcheck. First boot `migrate` races Postgres, `restart: always` hides the crash loop. | Add `pg_isready` healthcheck and `condition: service_healthy`. |
| `backend/docker-compose.yml` | med | Backend source bind-mounted (`./backend:/backend`) in the only compose file. Image is never used as built. | Move bind mount to a `docker-compose.override.yml` for dev. |
| `backend/backend/requirements.txt` | med | `Django` and `channels` not pinned. They come transitively from DRF/channels-redis, so a rebuild can jump major versions. No audit tool in this env (`pip-audit` missing); `requests==2.31.0` has CVE-2024-35195. | Pin `Django`, `channels`. Bump `requests>=2.32`. Run `pip-audit -r requirements.txt` in CI. |
| `settings.py:144-149` | med | User avatars served as static files (`STATIC_URL = "avatars/"`, `STATICFILES_DIRS`). Only works with `DEBUG=True` + runserver. Uploaded files are mixed with static assets. | Use `MEDIA_ROOT`/`MEDIA_URL` and serve media from nginx (volume). |
| `backend/nginx/nginx.conf` | med | Frontend `location /` commented out; frontend runs on `3001` over plain HTTP, API on `1337` over TLS. Hardcoded `localhost:8000` in frontend (see Phase 6) means nginx is bypassed in practice. No `/avatars/` location. Default `client_max_body_size` 1M limits avatar upload. | Serve frontend and avatars from nginx, single origin. Set `client_max_body_size`. |
| `backend/nginx/nginx.conf:41` | low | Port 80 redirect server exists but port 80 is not published. | Publish 80 or remove block. |
| `backend/nginx/Dockerfile:9` | low | Self-signed cert generated at build with `-subj "/"`. Fine for school eval, note only. Cert baked into image. | Mount certs from a volume. |
| `settings.py:85-92` | low | Redis without password, port from env but host hardcoded. | OK on private network; add `requirepass` if exposed. |
| `backend/docker-compose.yml` | low | Floating images (`postgres:alpine`, `redis:alpine`, `grafana/grafana`, `prom/prometheus`, `adminer`). Postgres major bump breaks the data volume. | Pin major versions (`postgres:16-alpine`). |
| `frontend/Dockerfile` | low | Runs `nodemon` (dev) as container CMD. `apk add yarn` is redundant (node image ships yarn). | `CMD ["node", "server.js"]`, drop apk line. |
| `frontend/docker-compose.yml` | low | Declares network `ft_transcendence` without `external: true`, while backend compose owns it. Start order decides who creates it. | Mark `external: true` in one file, or merge composes. |
| `backend/backend/ft_transcendence/urls.py:15` | low | `/` redirects to `api/` which has no route (404). | Remove redirect or point to a health endpoint. |
| `backend/create_accoutns.fish` | low | Dev seed script with hardcoded password, hits `localhost:8000` directly. Typo in filename. | Move to `scripts/`, rename, read password from env. |
| `settings.py:158` | info | `ACCESS_TOKEN_LIFETIME = 1 day`. Check usage in Phase 2. | - |

Not verified here: dependency CVE scan (no `pip-audit`/`yarn` installed locally).
