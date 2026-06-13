"""JSON persistence for analysis reports.

Serialises an :class:`EpicReport` to disk and reads it back. Useful for the
``--format json`` output, for caching results, and as the contract a future web
API or agent would consume.
"""

from __future__ import annotations

from pathlib import Path

from ai_engineering_metrics.domain.models import EpicReport


def report_to_json(report: EpicReport, *, indent: int = 2) -> str:
    """Serialise a report to a JSON string (datetimes as ISO 8601)."""
    return report.model_dump_json(indent=indent)


def save_report(report: EpicReport, path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(report_to_json(report), encoding="utf-8")
    return target


def load_report(path: str | Path) -> EpicReport:
    source = Path(path)
    return EpicReport.model_validate_json(source.read_text(encoding="utf-8"))
