# Server setup (once)

Any provider. Needs a Linux VPS (Ubuntu LTS here), a DNS name pointing at
it, and ports 22, 80 and 443 reachable. The server never builds anything: it
pulls the images CI pushed to GHCR.

## 1. Server

As root (or with sudo):

```bash
# Docker Engine + Compose plugin: https://docs.docker.com/engine/install/ubuntu/
apt-get install -y make

# Deploy user, SSH key login only.
adduser --disabled-password --gecos "" deploy
usermod -aG docker deploy
install -d -m 700 -o deploy -g deploy /home/deploy/.ssh
# Put the public half of the deploy key (step 3) in /home/deploy/.ssh/authorized_keys
install -d -o deploy -g deploy /srv/pong3d

# Firewall.
ufw allow OpenSSH && ufw allow 80/tcp && ufw allow 443/tcp && ufw enable
```

In `/etc/ssh/sshd_config`: `PasswordAuthentication no`, then `systemctl reload ssh`.

## 2. GHCR images

After the first CI run on main, open the two packages on GitHub
(`pong3d-backend`, `pong3d-nginx` under your profile > Packages) and set
their visibility to public once. Then the server pulls without logging in.
To keep them private instead, run on the server as `deploy`:
`docker login ghcr.io -u <github user>` with a token that has `read:packages`.

## 3. GitHub settings

Make a key pair for deploys only (no passphrase): `ssh-keygen -t ed25519 -f pong3d-deploy -C pong3d-deploy`.

Repository > Settings > Environments > New environment `production`
(optionally with required reviewers). Its secrets:

| Secret | Value |
| --- | --- |
| `VPS_HOST` | server address |
| `VPS_USER` | `deploy` |
| `VPS_SSH_KEY` | content of `pong3d-deploy` (private key) |
| `VPS_KNOWN_HOSTS` | output of `ssh-keyscan -t ed25519 <host>`, compared with `ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub` on the server |

Repository variables (Settings > Secrets and variables > Actions > Variables):

| Variable | Value |
| --- | --- |
| `DEPLOY_ENABLED` | `true` (the Deploy workflow does nothing without it) |
| `DEPLOY_PATH` | optional, default `/srv/pong3d` |
| `VPS_SSH_PORT` | optional, default `22` |

## 4. First deploy

1. Actions > Deploy > Run workflow, sha = the latest commit of main. It
   uploads the deploy files to `/srv/pong3d`, then stops: env files missing.
2. On the server, as `deploy`:
   ```bash
   cd /srv/pong3d
   make env ENV=prod DOMAIN=pong.example.org ACME_EMAIL=you@example.org
   # optional: INTRA_CLIENT_ID / INTRA_CLIENT_SECRET in env/prod/app.env
   ```
3. Run the Deploy workflow again (or `make deploy SHA=<sha>` on the server).
   The site answers on https with a temporary self-signed certificate.
4. Certificate: `make cert STAGING=1` (dry run), then `make cert`.
5. Nightly backup, `crontab -e` as `deploy`:
   ```
   0 3 * * * cd /srv/pong3d && make backup ENV=prod >> backups/backup.log 2>&1
   ```
6. 42 login: add `https://pong.example.org/api/auth/intra/callback/` to the intra app.

From then on every push to main that passes CI is deployed. See the README
("Deploys and rollback") for rollbacks and limits.
