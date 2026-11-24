# Entry point for the whole stack. `make` lists the targets.
#
# ENV picks the overlay: compose.yaml + compose.$(ENV).yaml (dev or prod).
ENV ?= dev
COMPOSE := docker compose -f compose.yaml -f compose.$(ENV).yaml
TEST_COMPOSE := docker compose -f compose.test.yaml

.DEFAULT_GOAL := help
.PHONY: help env dev prod up down restart logs ps test

help: ## List the targets
	@awk 'BEGIN {FS = ":.*## "} /^[a-z-]+:.*## / {printf "  make %-8s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

env: ## Create .env (random secrets; keeps an existing one)
	@sh infra/scripts/gen-env.sh

.env:
	@sh infra/scripts/gen-env.sh

dev: ## Build and start the dev stack on https://localhost:1337
	@$(MAKE) --no-print-directory up ENV=dev

prod: ## Build and start the prod stack (images only, no bind mounts)
	@$(MAKE) --no-print-directory up ENV=prod

up: .env
	$(COMPOSE) up -d --build --remove-orphans
	@echo "Up: https://localhost:1337  (make logs to follow, make down to stop)"

down: ## Stop and remove the containers (data volumes are kept)
	$(COMPOSE) down --remove-orphans

restart: ## Restart a service: make restart s=backend
	$(COMPOSE) restart $(s)

logs: ## Follow logs: make logs [s=backend]
	$(COMPOSE) logs -f --tail=100 $(s)

ps: ## Show the containers
	$(COMPOSE) ps

test: ## Run the backend tests against a throwaway Postgres
	@$(TEST_COMPOSE) run --rm --build tests; status=$$?; \
		$(TEST_COMPOSE) down -v --remove-orphans >/dev/null 2>&1; \
		exit $$status
