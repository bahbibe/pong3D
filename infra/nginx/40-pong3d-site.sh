#!/bin/sh
# Run by the nginx image's entrypoint before nginx starts. Installs the dev
# or prod server config (NGINX_SITE, default dev).
set -eu
case "${NGINX_SITE:-dev}" in
    prod)
        : "${DOMAIN:?DOMAIN must be set (env/prod/nginx.env)}"
        export HSTS_MAX_AGE="${HSTS_MAX_AGE:-31536000}"
        envsubst '${DOMAIN} ${HSTS_MAX_AGE}' \
            < /etc/nginx/pong3d/prod.conf.template > /etc/nginx/conf.d/default.conf
        pong3d-select-cert
        # certbot renews in its own container; pick up new certificates.
        ( while sleep 6h; do pong3d-select-cert && nginx -s reload; done ) &
        ;;
    dev)
        cp /etc/nginx/pong3d/dev.conf /etc/nginx/conf.d/default.conf
        ;;
    *)
        echo "NGINX_SITE must be dev or prod" >&2
        exit 1
        ;;
esac
