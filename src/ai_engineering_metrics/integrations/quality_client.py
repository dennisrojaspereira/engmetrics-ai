"""Quality metrics source.

For now quality data comes either from a JSON file exported by a static-analysis
tool (e.g. SonarQube) or from mocked values. The interface is intentionally
small so a real SonarQube/CodeClimate client can be dropped in later without
touching the rest of the system.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ai_engineering_metrics.domain.models import QualityMetrics
from ai_engineering_metrics.integrations.base import IntegrationError

# Maps incoming JSON keys (several common conventions) to model fields.
_FIELD_ALIASES = {
    "cyclomatic_complexity": "cyclomatic_complexity",
    "complexity": "cyclomatic_complexity",
    "cognitive_complexity": "cognitive_complexity",
    "duplication_percent": "duplication_percent",
    "duplicated_lines_density": "duplication_percent",
    "code_smells": "code_smells",
    "static_bugs": "static_bugs",
    "bugs": "static_bugs",
    "vulnerabilities": "vulnerabilities",
    "test_coverage_percent": "test_coverage_percent",
    "coverage": "test_coverage_percent",
}


class JsonQualityClient:
    """Loads quality metrics from a JSON file on disk."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    def get_quality_metrics(self) -> QualityMetrics:
        if not self._path.exists():
            raise IntegrationError(f"Quality metrics file not found: {self._path}")
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise IntegrationError(f"Invalid JSON in quality metrics file: {exc}") from exc

        mapped: dict[str, Any] = {}
        for key, value in raw.items():
            field = _FIELD_ALIASES.get(key)
            if field:
                mapped[field] = value
        mapped["source"] = "json"
        return QualityMetrics(**mapped)


class NullQualityClient:
    """Used when no quality source is configured: returns empty metrics."""

    def get_quality_metrics(self) -> QualityMetrics:
        return QualityMetrics(source="unavailable")
