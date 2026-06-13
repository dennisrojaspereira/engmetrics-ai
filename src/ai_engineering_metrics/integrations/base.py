"""Shared HTTP plumbing and client protocols.

``HttpClient`` wraps httpx with sane defaults: timeouts, transparent retries
with exponential backoff, and rate-limit handling (HTTP 429 / GitHub's
``X-RateLimit-Remaining``). Secrets are never logged.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Protocol, runtime_checkable

import httpx

from ai_engineering_metrics.domain.models import Epic, PullRequest, QualityMetrics, Story

logger = logging.getLogger("ai_engineering_metrics")

MAX_RETRIES = 4
BACKOFF_BASE_SECONDS = 1.5


class IntegrationError(RuntimeError):
    """Raised when an external system cannot satisfy a request."""


class NotFoundError(IntegrationError):
    """Raised when a requested resource (e.g. an epic) does not exist."""


class HttpClient:
    """Thin, retry-aware wrapper around an ``httpx.Client``."""

    def __init__(
        self,
        base_url: str,
        *,
        headers: dict[str, str] | None = None,
        auth: tuple[str, str] | None = None,
        timeout: float = 30.0,
    ) -> None:
        self._client = httpx.Client(
            base_url=base_url,
            headers=headers or {},
            auth=auth,
            timeout=timeout,
        )

    def __enter__(self) -> HttpClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()

    def get(self, path: str, **kwargs: Any) -> httpx.Response:
        return self._request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> httpx.Response:
        return self._request("POST", path, **kwargs)

    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        last_exc: Exception | None = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = self._client.request(method, path, **kwargs)
            except httpx.TransportError as exc:  # network blip
                last_exc = exc
                self._sleep_backoff(attempt, reason=str(exc))
                continue

            if response.status_code == 429 or _rate_limited(response):
                wait = _retry_after(response, attempt)
                logger.warning("Rate limited on %s; waiting %.1fs before retry", path, wait)
                time.sleep(wait)
                continue

            if 500 <= response.status_code < 600:
                last_exc = IntegrationError(f"{response.status_code} from {path}")
                self._sleep_backoff(attempt, reason=f"server error {response.status_code}")
                continue

            if response.status_code == 404:
                raise NotFoundError(f"Resource not found: {path}")

            if response.status_code >= 400:
                # Do not include response body blindly; it may echo back tokens.
                raise IntegrationError(
                    f"Request to {path} failed with status {response.status_code}"
                )

            return response

        raise IntegrationError(
            f"Request to {path} failed after {MAX_RETRIES} attempts"
        ) from last_exc

    @staticmethod
    def _sleep_backoff(attempt: int, *, reason: str) -> None:
        wait = BACKOFF_BASE_SECONDS * (2 ** (attempt - 1))
        logger.warning("Retry %d after %.1fs (%s)", attempt, wait, reason)
        time.sleep(wait)


def _rate_limited(response: httpx.Response) -> bool:
    remaining = response.headers.get("X-RateLimit-Remaining")
    return remaining == "0" and response.status_code in {403, 429}


def _retry_after(response: httpx.Response, attempt: int) -> float:
    header = response.headers.get("Retry-After")
    if header and header.isdigit():
        return float(header)
    reset = response.headers.get("X-RateLimit-Reset")
    if reset and reset.isdigit():
        # Best-effort; clamp so we never sleep absurdly long in a CLI run.
        return min(60.0, max(1.0, float(reset) % 60))
    return BACKOFF_BASE_SECONDS * (2 ** (attempt - 1))


@runtime_checkable
class IssueSource(Protocol):
    """Anything that can resolve an epic and its stories (JIRA today)."""

    def get_epic(self, epic_key: str) -> Epic: ...

    def get_stories(self, epic_key: str) -> list[Story]: ...


@runtime_checkable
class PullRequestSource(Protocol):
    """Anything that can find PRs linked to an issue key (GitHub today)."""

    def find_pull_requests(self, issue_key: str) -> list[PullRequest]: ...


@runtime_checkable
class QualitySource(Protocol):
    """Anything that can supply static-analysis quality metrics."""

    def get_quality_metrics(self) -> QualityMetrics: ...
