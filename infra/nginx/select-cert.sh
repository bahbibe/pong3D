#!/bin/sh
# Point /etc/nginx/certs/current at the Let's Encrypt certificate for
# $DOMAIN when it exists, else at the self-signed one baked into the image.
# Run at start, by `make cert` after issuing, and before each periodic reload.
set -eu
live=/etc/letsencrypt/live/${DOMAIN:?}
if [ -s "$live/fullchain.pem" ] && [ -s "$live/privkey.pem" ]; then
    target=$live
else
    target=/etc/nginx/ssl
fi
mkdir -p /etc/nginx/certs
ln -sfn "$target" /etc/nginx/certs/current
echo "pong3d: TLS certificate from $target"
