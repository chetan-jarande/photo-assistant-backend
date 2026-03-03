# Default command when you just type "make"
.DEFAULT_GOAL := help

PYTHON_VERSION=3.13.0
VENV_ROOT=./.venv
PROJECT_NAME=photo-assistant-backend

ifeq ($(shell command -v pyenv),)
	PYENV_BIN=$(HOME)/.pyenv/bin/pyenv
else
	PYENV_BIN=pyenv
endif

export CONF_ENV?=dev

venv:
	@echo "Using pyenv from '$(PYENV_BIN)'"
	find . -type d -name '*__pycache__*' | xargs rm -rf
	"$(PYENV_BIN)" install --skip-existing "$(PYTHON_VERSION)"
	"$(PYENV_BIN)" local "$(PYTHON_VERSION)"
	"$(PYENV_BIN)" exec python -m venv --clear --upgrade-deps "$(VENV_ROOT)"
	"$(PYENV_BIN)" local --unset
	@echo "Installing uv tool..."
	@"$(VENV_ROOT)/bin/pip" install --upgrade uv

deps: venv
	"$(VENV_ROOT)/bin/uv" pip install -e '.'

dev: venv
	"$(VENV_ROOT)/bin/uv" pip install -e '.[dev]'

test-local: dev
	"$(VENV_ROOT)/bin/pytest" -vvv

test:
	docker-compose -p $(PROJECT_NAME) exec api pytest -vvv

build: venv
	"$(VENV_ROOT)/bin/pip" install --upgrade build
	rm -rf ./dist/
	"$(VENV_ROOT)/bin/python" -m build --wheel --outdir ./dist/

# Generic run command for use inside Docker containers
#TODO: Update it to follow python -m app.main
run:
	uvicorn main:app --host 0.0.0.0 --port 8000

# Command for local venv usage
run-local:
	"$(VENV_ROOT)/bin/python" -m 'app.main'

inspector:
	npx @modelcontextprotocol/inspector --config inspector.mcp.json --server local-server

# Build the docker images
docker-build:
	docker-compose -p $(PROJECT_NAME) build

# Build without cache
docker-build-fresh:
	docker-compose -p $(PROJECT_NAME) build --no-cache

# Start the services in detached mode
docker-up:
	docker-compose -p $(PROJECT_NAME) up -d

# Stop and remove the services, networks, volumes, and orphans
docker-down:
	docker-compose -p $(PROJECT_NAME) down --volumes --remove-orphans

# Restart the services
docker-restart: docker-down docker-up

# Prune Docker system (use with caution)
docker-prune:
	docker system prune -f

# View the logs from the services
docker-logs:
	docker-compose -p $(PROJECT_NAME) logs -f

# Access a shell inside the running api container
docker-shell:
	docker-compose -p $(PROJECT_NAME) exec api /bin/bash

# Show this help message
help:
	@echo "Usage: make [command]"
	@echo "Commands:"
	@echo "  venv                Create virtual environment"
	@echo "  deps                Install dependencies"
	@echo "  dev                 Install dev dependencies"
	@echo "  test-local          Run tests locally"
	@echo "  test                Run tests in docker"
	@echo "  build               Build wheel"
	@echo "  run-local           Run locally with uvicorn"
	@echo "  inspector           Run MCP inspector"
	@echo "  docker-build        Build docker images"
	@echo "  docker-up           Start docker services"
	@echo "  docker-down         Stop docker services"
	@echo "  docker-logs         View docker logs"
	@echo "  docker-shell        Shell into api container"

.PHONY: venv deps dev test-local test build run run-local inspector docker-build docker-build-fresh docker-up docker-down docker-restart docker-logs docker-shell help
