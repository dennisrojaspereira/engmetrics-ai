# syntax=docker/dockerfile:1
# ---------------------------------------------------------------------------
# Reproducible local dev / test image for ai-engineering-metrics.
# Targets mock-mode runs, tests and the quality/security tooling. Real GitHub
# runs use the host's `gh` CLI (auth lives on the host), not this container.
# ---------------------------------------------------------------------------
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install dependencies first for better layer caching.
COPY pyproject.toml README.md ./
COPY src ./src
RUN python -m pip install --upgrade pip && python -m pip install -e ".[dev]"

# Copy the rest of the project (tests, configs, data, etc.).
COPY . .

# Run as a non-root user.
RUN useradd --create-home --uid 1000 appuser \
    && mkdir -p /app/generated /app/reports \
    && chown -R appuser:appuser /app
USER appuser

# Default: print CLI help. Override per command, e.g.:
#   docker compose run --rm app pytest
CMD ["ai-engineering-metrics", "--help"]
