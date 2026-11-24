#!/bin/sh
# Create group_vars/pong3d/vault.yml with random secrets, encrypted
# (called by `make vault-new`). ansible-vault asks for a new vault password,
# unless ANSIBLE_VAULT_PASSWORD_FILE is set.
set -eu
cd "$(dirname "$0")"
vault=group_vars/pong3d/vault.yml

if [ -e "$vault" ]; then
    echo "$vault already exists. Edit it with: make vault-edit" >&2
    exit 1
fi

random_hex() { openssl rand -hex 32; }

umask 077
mkdir -p group_vars/pong3d
tmp=$(mktemp "$vault.XXXXXX")
trap 'rm -f "$tmp"' EXIT
cat > "$tmp" <<EOF
# Prod secrets for pong3D (encrypted with ansible-vault; see vault.yml.example).
vault_django_secret_key: "$(random_hex)"
vault_jwt_secret: "$(random_hex)"
vault_postgres_password: "$(random_hex)"
vault_redis_password: "$(random_hex)"
vault_grafana_admin_password: "$(random_hex)"
# 42 intra OAuth app (optional): fill in with make vault-edit.
vault_intra_client_id: ""
vault_intra_client_secret: ""
EOF

ansible-vault encrypt "$tmp" --output "$vault"
echo "Created $vault (encrypted). Commit it; keep the vault password in a password manager."
