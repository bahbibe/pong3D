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

.DEFAULT_GOAL := help
.PHONY: help env dev prod up down restart logs ps migrate test tools tools-down cert backup restore deploy

help: ## List the targets
	@awk 'BEGIN {FS = ":.*## "} /^[a-z-]+:.*## / {printf "  make %-11s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

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

cert: ## Prod: get the Let's Encrypt certificate for DOMAIN (STAGING=1 to test)
	@set -a; . env/prod/nginx.env; set +a; \
	test -n "$$DOMAIN" -a -n "$$ACME_EMAIL" || { echo "Set DOMAIN and ACME_EMAIL in env/prod/nginx.env" >&2; exit 2; }; \
	$(PROD_COMPOSE) run --rm --entrypoint certbot certbot certonly --webroot -w /var/www/certbot \
		-d "$$DOMAIN" -m "$$ACME_EMAIL" --agree-tos --no-eff-email --non-interactive \
		$(if $(STAGING),--staging) && \
	$(PROD_COMPOSE) exec nginx sh -c 'pong3d-select-cert && nginx -s reload'

backup: ## Dump the database and avatars to backups/ (keeps 7)
	@COMPOSE="$(COMPOSE)" sh infra/scripts/backup.sh

restore: ## Restore: make restore FILE=backups/db-<time>.dump [AVATARS=...tgz]
	@COMPOSE="$(COMPOSE)" FILE="$(FILE)" AVATARS="$(AVATARS)" sh infra/scripts/restore.sh

deploy: ## Server: deploy or roll back to a commit's images: make deploy SHA=<sha>
	@sh infra/scripts/deploy.sh $(SHA)
