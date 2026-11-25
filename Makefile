# Entry point for the whole stack. `make` lists the targets.
#
# ENV picks the overlay and the env folder: compose.yaml + compose.$(ENV).yaml,
# env/$(ENV)/*.env (dev or prod).
ENV ?= dev
export PONG3D_ENV := $(ENV)
COMPOSE := docker compose -f compose.yaml -f compose.$(ENV).yaml
PROD_COMPOSE := PONG3D_ENV=prod docker compose -f compose.yaml -f compose.prod.yaml
TEST_COMPOSE := docker compose -f compose.test.yaml
TOOLS := prometheus grafana $(if $(filter dev,$(ENV)),adminer)
# uv in a container (same version as the Dockerfile and CI): no local
# Python or uv needed for `make lock`.
# LOCK_DIR=e2e locks the e2e tests instead of the backend.
LOCK_DIR ?= backend
UV := docker run --rm -u "$$(id -u):$$(id -g)" -v "$(CURDIR)/$(LOCK_DIR):/project" -w /project \
	-e UV_CACHE_DIR=/tmp/uv-cache ghcr.io/astral-sh/uv:0.11.32-python3.12-alpine uv

.DEFAULT_GOAL := help
.PHONY: help env dev prod up down restart logs ps migrate test e2e openapi lock tools tools-down cert backup restore deploy provision provision-check vault-new vault-edit

help: ## List the targets
	@awk 'BEGIN {FS = ":.*## "} /^[a-z0-9-]+:.*## / {printf "  make %-16s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

env: ## Create .env and env/$(ENV)/*.env (prod: DOMAIN=... ACME_EMAIL=...)
	@ENV=$(ENV) DOMAIN="$(DOMAIN)" ACME_EMAIL="$(ACME_EMAIL)" sh infra/scripts/gen-env.sh

env/%/app.env:
	@ENV=$* DOMAIN="$(DOMAIN)" ACME_EMAIL="$(ACME_EMAIL)" sh infra/scripts/gen-env.sh

dev: ## Build and start the dev stack on https://localhost:1337
	@$(MAKE) --no-print-directory up ENV=dev

prod: ## Build and start the prod stack from source (on a server: make deploy)
	@$(MAKE) --no-print-directory up ENV=prod

up: env/$(ENV)/app.env
	$(COMPOSE) up -d --build --remove-orphans --wait
	@echo "Up ($(ENV)). make logs to follow, make down to stop."

down: ## Stop and remove the containers, tools included (volumes are kept)
	$(COMPOSE) --profile tools down --remove-orphans

restart: ## Restart a service: make restart s=backend
	$(COMPOSE) restart $(s)

logs: ## Follow logs: make logs [s=backend]
	$(COMPOSE) logs -f --tail=100 $(s)

ps: ## Show the containers and their health
	$(COMPOSE) ps -a

migrate: ## Apply migrations now (they also run on every make dev/prod)
	$(COMPOSE) run --rm migrate

tools: env/$(ENV)/app.env ## Start grafana :3000, prometheus (+ adminer :8080 in dev) on 127.0.0.1
	$(COMPOSE) --profile tools up -d --no-deps $(TOOLS)

tools-down: ## Stop the tools only
	$(COMPOSE) --profile tools rm -sf $(TOOLS)

test: ## Run the backend tests against a throwaway Postgres
	@$(TEST_COMPOSE) run --rm --build tests; status=$$?; \
		$(TEST_COMPOSE) down -v --remove-orphans >/dev/null 2>&1; \
		exit $$status

e2e: ## Browser and websocket tests against the running stack (make dev first; needs uv)
	@command -v uv >/dev/null || { echo "make e2e needs uv on this machine: https://docs.astral.sh/uv/" >&2; exit 2; }
	cd e2e && uv sync --frozen && uv run --no-sync playwright install chromium && \
		E2E_COMPOSE="$(COMPOSE)" uv run --no-sync pytest $(ARGS)

openapi: ## Write docs/openapi.yaml from the code (CI checks it is up to date)
	$(COMPOSE) run --rm --no-deps -T --entrypoint python backend manage.py spectacular --validate --fail-on-warn \
		> docs/openapi.yaml.tmp && mv docs/openapi.yaml.tmp docs/openapi.yaml

lock: ## Update backend/uv.lock after editing pyproject.toml (LOCK_DIR=e2e: the e2e lock; one package: ARGS="--upgrade-package django")
	$(UV) lock $(ARGS)

cert: ## Prod: get the Let's Encrypt certificate for DOMAIN (STAGING=1: dry run, saves nothing)
	@set -a; . env/prod/nginx.env; set +a; \
	test -n "$$DOMAIN" -a -n "$$ACME_EMAIL" || { echo "Set DOMAIN and ACME_EMAIL in env/prod/nginx.env" >&2; exit 2; }; \
	$(PROD_COMPOSE) run --rm --entrypoint certbot certbot certonly --webroot -w /var/www/certbot \
		-d "$$DOMAIN" -m "$$ACME_EMAIL" --agree-tos --no-eff-email --non-interactive \
		$(if $(STAGING),--dry-run) && \
	$(PROD_COMPOSE) exec nginx sh -c 'pong3d-select-cert && nginx -s reload'

backup: ## Dump the database and avatars to backups/ (keeps 7)
	@COMPOSE="$(COMPOSE)" sh infra/scripts/backup.sh

restore: ## Restore: make restore FILE=backups/db-<time>.dump [AVATARS=...tgz]
	@COMPOSE="$(COMPOSE)" FILE="$(FILE)" AVATARS="$(AVATARS)" sh infra/scripts/restore.sh

deploy: ## Server: deploy or roll back to a commit's images: make deploy SHA=<sha>
	@sh infra/scripts/deploy.sh $(SHA)

# --- Server provisioning (Ansible, run from your machine) -------------------
# Inventory: infra/ansible/inventory/prod.yml. Vault password: asked, or
# ANSIBLE_VAULT_PASSWORD_FILE. Extra arguments: ARGS="--tags app".
ANSIBLE := cd infra/ansible && ansible-playbook site.yml $(if $(ANSIBLE_VAULT_PASSWORD_FILE),,--ask-vault-pass)

provision: ## Provision the server with Ansible (infra/ansible, see docs/bootstrap-vps.md)
	$(ANSIBLE) $(ARGS)

provision-check: ## Dry run of make provision (shows what would change)
	$(ANSIBLE) --check --diff $(ARGS)

vault-new: ## Create the encrypted Ansible vault with random prod secrets
	@sh infra/ansible/new-vault.sh

vault-edit: ## Edit the Ansible vault (42 intra secret, passwords)
	cd infra/ansible && ansible-vault edit group_vars/pong3d/vault.yml
