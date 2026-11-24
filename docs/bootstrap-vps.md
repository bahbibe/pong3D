# Server setup

Any provider. Needs an x86_64 Linux VPS with Ubuntu 24.04 LTS, root SSH
access with your key, a DNS name pointing at it, and ports 22, 80 and 443
reachable. The server never builds anything: it pulls the images CI pushed
to GHCR.

Provisioning is done by the Ansible playbook in `infra/ansible/`, run from
your machine. It is idempotent: run it again after changing a variable or
a secret.

| Ansible role | What it does |
| --- | --- |
| `base` | packages, unattended security upgrades (no automatic reboot), swap file |
| `deploy_user` | `deploy` user in the docker group, SSH keys only |
| `ssh` | no passwords, root by key only |
| `firewall` | ufw: only 22, 80, 443 in |
| `docker` | Docker Engine + Compose plugin from Docker's apt repo, container log rotation |
| `app` | `/srv/pong3d` (compose files, Makefile, scripts), `env/prod/*.env` from the vault, nightly backup cron, Let's Encrypt certificate once deployed |

Deploys are not part of it: the Deploy workflow runs `infra/scripts/deploy.sh`.

## 1. Your machine

Ansible 2.15+ and its collections:

```bash
ansible-galaxy collection install -r infra/ansible/requirements.yml
```

A key pair for deploys only (no passphrase), used by GitHub Actions:

```bash
ssh-keygen -t ed25519 -f ~/.ssh/pong3d-deploy -C pong3d-deploy
```

## 2. Inventory and vault

```bash
cp infra/ansible/inventory/prod.yml.example infra/ansible/inventory/prod.yml
# edit: ansible_host, domain, acme_email, deploy_authorized_keys
#       (the content of ~/.ssh/pong3d-deploy.pub and your own public key)

make vault-new     # random prod secrets in infra/ansible/group_vars/pong3d/vault.yml, encrypted
make vault-edit    # optional: vault_intra_client_id / vault_intra_client_secret
```

The vault file is committed, and the repository is **public**: pick a long
random vault password (`openssl rand -base64 32`) and keep it in a password
manager. The playbook refuses to run if the vault file is not encrypted. To
avoid typing the password: `export ANSIBLE_VAULT_PASSWORD_FILE=~/.pong3d-vault-pass`
(a file only you can read, never in the repo).

Changing `vault_postgres_password` after the first deploy does not change the
existing database user's password: run `ALTER USER` in the db container first.

## 3. Provision

```bash
make provision-check   # dry run: what would change
make provision         # do it
```

Extra arguments go through `ARGS`, for example `make provision ARGS="--tags app"`.

## 4. GitHub settings

Repository > Settings > Environments > New environment `production`
(optionally with required reviewers). Its secrets:

| Secret | Value |
| --- | --- |
| `VPS_HOST` | server address |
| `VPS_USER` | `deploy` |
| `VPS_SSH_KEY` | content of `~/.ssh/pong3d-deploy` (private key) |
| `VPS_KNOWN_HOSTS` | output of `ssh-keyscan -t ed25519 <host>`, compared with `ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub` on the server |

Repository variables (Settings > Secrets and variables > Actions > Variables):

| Variable | Value |
| --- | --- |
| `DEPLOY_ENABLED` | `true` (the Deploy workflow does nothing without it) |
| `DEPLOY_PATH` | optional, default `/srv/pong3d` |
| `VPS_SSH_PORT` | optional, default `22` |

The GHCR images (`ghcr.io/bahbibe/pong3d-backend`, `pong3d-nginx`) are public,
so the server pulls them without logging in.

## 5. First deploy and certificate

1. Actions > Deploy > Run workflow, sha = the latest commit of main (or on
   the server: `cd /srv/pong3d && make deploy SHA=<sha>`). The site answers on
   https with a temporary self-signed certificate.
2. `make provision` again: now that nginx runs, it gets the Let's Encrypt
   certificate. To test first, set `letsencrypt_staging: true` in the
   inventory: certbot then does a dry run against the staging server and
   saves nothing; remove the setting and run again for the real one.
3. 42 login: add `https://<domain>/api/auth/intra/callback/` to the intra app.

From then on every push to main that passes CI is deployed. See the README
("Deploys and rollback") for rollbacks and limits.

## Without Ansible

The same by hand: Docker Engine + Compose plugin, a `deploy` user in the
docker group with the deploy key, ufw (22, 80, 443), `/srv/pong3d` owned by
`deploy`. Run the Deploy workflow once (it uploads the files, then stops:
no env files), then on the server as `deploy`:
`make env ENV=prod DOMAIN=... ACME_EMAIL=...`, deploy again, `make cert`, and
add the backup cron line from the README.
