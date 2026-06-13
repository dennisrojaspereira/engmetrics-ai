# ai-engineering-metrics — developer tasks
# Usage: `make <target>` (needs GNU Make; on Windows use Git Bash/WSL or the
# equivalent `python -m ...` commands shown in each recipe).

PY ?= python

.DEFAULT_GOAL := help
.PHONY: help install lint format typecheck test cov security audit secrets \
        precommit demo docker-build docker-test all clean

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN{FS=":.*## "}{printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

install: ## Install the package with dev dependencies
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -e ".[dev]"
	$(PY) -m pre_commit install || true

lint: ## Lint with ruff
	$(PY) -m ruff check .

format: ## Auto-format with ruff
	$(PY) -m ruff format .
	$(PY) -m ruff check . --fix

typecheck: ## Static type-check with mypy
	$(PY) -m mypy

test: ## Run unit tests
	$(PY) -m pytest

cov: ## Run tests with coverage
	$(PY) -m pytest --cov=ai_engineering_metrics --cov-report=term-missing

security: ## SAST with bandit
	$(PY) -m bandit -c pyproject.toml -r src

audit: ## Dependency vulnerability scan
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip_audit

secrets: ## Secret scan (requires gitleaks on PATH)
	gitleaks detect --no-banner --redact

precommit: ## Run all pre-commit hooks on all files
	$(PY) -m pre_commit run --all-files

demo: ## Generate the sanitized mock demo dashboard
	$(PY) -m ai_engineering_metrics analyze --epic DEMO-1 --mock --output ./generated/demo.html

docker-build: ## Build the dev/test image
	docker compose build

docker-test: ## Run the full suite in Docker (like CI)
	docker compose -f docker-compose.test.yml run --rm test

all: lint format typecheck test security ## Run the core local gate

clean: ## Remove caches and build artifacts
	rm -rf .pytest_cache .ruff_cache .mypy_cache .coverage htmlcov build dist *.egg-info
	find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
