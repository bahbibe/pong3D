# Build context: the repo root (see compose.yaml). Only the files listed in
# Dockerfile.dockerignore are sent: this folder and the frontend.
FROM nginx:1.31.9-alpine

# Self-signed certificate: dev (https://localhost:1337) and the prod fallback
# until Let's Encrypt issued one.
RUN apk add --no-cache openssl \
    && mkdir -p /etc/nginx/ssl /etc/nginx/certs /var/www/certbot \
    && openssl req -x509 -nodes -days 825 -newkey rsa:2048 \
        -keyout /etc/nginx/ssl/privkey.pem -out /etc/nginx/ssl/fullchain.pem \
        -subj "/CN=localhost" -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"

# Config pieces; 40-pong3d-site.sh installs dev.conf or prod.conf.template
# as conf.d/default.conf at start (NGINX_SITE=dev|prod).
COPY infra/nginx/common.conf infra/nginx/headers.conf infra/nginx/dev.conf \
     infra/nginx/prod.conf.template /etc/nginx/pong3d/
COPY infra/nginx/select-cert.sh /usr/local/bin/pong3d-select-cert
COPY infra/nginx/40-pong3d-site.sh /docker-entrypoint.d/
RUN chmod +x /usr/local/bin/pong3d-select-cert /docker-entrypoint.d/40-pong3d-site.sh \
    && rm -f /etc/nginx/conf.d/default.conf

# The SPA. In dev, compose.dev.yaml mounts ./frontend over this folder.
COPY frontend/index.html /srv/frontend/index.html
COPY frontend/static /srv/frontend/static
