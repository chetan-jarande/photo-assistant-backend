# Default command when you just type "make"
.DEFAULT_GOAL := help

PYTHON_VERSION=3.13.12
VENV_ROOT=.venv
PROJECT_NAME=photo-assistant-backend

export CONF_ENV?=dev

# Check for uv installation
UV_BIN := $(shell command -v uv 2> /dev/null)

check-uv:
ifndef UV_BIN
	$(error "uv is not installed. Please install it: curl -LsSf https://astral.sh/uv/install.sh | sh")
endif

# Environment Setup
venv: check-uv
	@echo "Using uv for environment management"
	rm -rf $(VENV_ROOT)
	uv venv --python $(PYTHON_VERSION) $(VENV_ROOT)
	@echo "Virtual environment created at $(VENV_ROOT)"

# Dependency Management
deps: venv
	uv pip install -e .

dev: venv
	uv pip install -e '.[dev]'

# Testing
test-local: dev
	uv run pytest -vvv

test:
	docker-compose -p $(PROJECT_NAME) exec api uv run pytest -vvv

# Building
build: venv
	uv pip install build
	rm -rf ./dist/
	uv run python -m build --wheel --outdir ./dist/

# Running Locally
run:
	uv run uvicorn main:app --host 0.0.0.0 --port 8000

run-local:
	uv run python main.py

# MCP Inspector
inspector:
	npx @modelcontextprotocol/inspector --config inspector.mcp.json --server local-server

# Docker Operations
docker-build:
	docker-compose -p $(PROJECT_NAME) build

docker-build-fresh:
	docker-compose -p $(PROJECT_NAME) build --no-cache

docker-up:
	docker-compose -p $(PROJECT_NAME) up -d

docker-down:
	docker-compose -p $(PROJECT_NAME) down --volumes --remove-orphans

docker-restart: docker-down docker-up

docker-prune:
	docker system prune -f

docker-logs:
	docker-compose -p $(PROJECT_NAME) logs -f

docker-shell:
	docker-compose -p $(PROJECT_NAME) exec api /bin/bash

# Help
help:
	@echo "Usage: make [command]"
	@echo "Commands:"
	@echo "  venv                Create virtual environment using uv"
	@echo "  deps                Install dependencies using uv"
	@echo "  dev                 Install dev dependencies using uv"
	@echo "  test-local          Run tests locally using uv run"
	@echo "  test                Run tests in docker"
	@echo "  build               Build wheel using uv run"
	@echo "  run                 Run uvicorn using uv run"
	@echo "  run-local           Run locally using uv run python -m app.main"
	@echo "  inspector           Run MCP inspector"
	@echo "  docker-build        Build docker images"
	@echo "  docker-up           Start docker services"
	@echo "  docker-down         Stop docker services"
	@echo "  docker-logs         View docker logs"
	@echo "  docker-shell        Shell into api container"

.PHONY: check-uv venv deps dev test-local test build run run-local inspector docker-build docker-build-fresh docker-up docker-down docker-restart docker-logs docker-shell help
