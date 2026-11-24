# Stage 1: Python dependencies in a virtualenv (copied into the runtime
# image), installed from uv.lock exactly (no resolving at build time).
FROM python:3.12.16-alpine3.24 AS deps

COPY --from=ghcr.io/astral-sh/uv:0.11.32 /uv /usr/local/bin/uv
ENV UV_PROJECT_ENVIRONMENT=/venv \
    UV_PYTHON_DOWNLOADS=never \
    UV_PYTHON=/usr/local/bin/python3 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_CACHE=1

COPY pyproject.toml uv.lock /tmp/project/
WORKDIR /tmp/project

# DEV=1 (compose.dev.yaml) adds the dev group (the reload tool). Prod and
# test images skip it.
ARG DEV=0
RUN if [ "$DEV" = "1" ]; then uv sync --frozen; else uv sync --frozen --no-dev; fi


# Stage 2: runtime.
FROM python:3.12.16-alpine3.24

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/venv/bin:$PATH"

# Unprivileged user. The code stays owned by root (read-only for the app);
# only the avatars folder is writable. In prod it is a named volume, which
# copies this folder (default avatar and ownership) on first use.
RUN addgroup -S -g 10001 app && adduser -S -D -H -u 10001 -G app app

COPY --from=deps /venv /venv

WORKDIR /backend
COPY . .
RUN chown -R app:app /backend/media/avatars

USER app
EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]

# Prod: daphne without reload, so running games (in memory) are not killed
# by file changes. Dev overrides this command with a reloading one.
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "--proxy-headers", "config.asgi:application"]
