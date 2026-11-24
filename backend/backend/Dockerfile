# Stage 1: Python dependencies in a virtualenv (copied into the runtime image).
FROM python:3.12.16-alpine3.24 AS deps

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1

COPY requirements.txt requirements-dev.txt /tmp/
RUN python -m venv /venv && /venv/bin/pip install -r /tmp/requirements.txt

# DEV=1 (compose.dev.yaml) adds the reload tool. Prod and test images skip it.
ARG DEV=0
RUN if [ "$DEV" = "1" ]; then /venv/bin/pip install -r /tmp/requirements-dev.txt; fi


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
RUN chown -R app:app /backend/avatars

USER app
EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]

# Prod: daphne without reload, so running games (in memory) are not killed
# by file changes. Dev overrides this command with a reloading one.
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "--proxy-headers", "ft_transcendence.asgi:application"]
