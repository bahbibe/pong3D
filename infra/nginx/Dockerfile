# Build context: the repo root (see compose.yaml). Only the files listed in
# Dockerfile.dockerignore are sent: this folder and the frontend.
FROM nginx:alpine

# Self-signed certificate for https://localhost:1337 (dev and local prod).
RUN apk add --no-cache openssl \
    && mkdir -p /etc/nginx/ssl \
    && openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout /etc/nginx/ssl/nginx.key -out /etc/nginx/ssl/nginx.crt \
        -subj "/CN=localhost" -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"

# Replaces the image's default server (it also listened on port 80).
COPY infra/nginx/nginx.conf /etc/nginx/conf.d/default.conf

# The SPA. In dev, compose.dev.yaml mounts ./frontend over this folder.
COPY frontend/index.html /srv/frontend/index.html
COPY frontend/static /srv/frontend/static
