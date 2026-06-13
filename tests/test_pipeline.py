"""End-to-end tests using the mock data sources (no network)."""

from pathlib import Path

from ai_engineering_metrics.config import Settings
from ai_engineering_metrics.reports.html_report import render_html
from ai_engineering_metrics.service import AnalysisService
from ai_engineering_metrics.storage.json_storage import load_report, save_report


def _report():
    service = AnalysisService.for_settings(Settings(), mock=True)
    return service.analyze("KAN-20001")


def test_mock_analysis_shape():
    report = _report()
    assert report.epic.key == "KAN-20001"
    assert len(report.stories) == 5
    assert len(report.all_pull_requests) == 8
    assert report.ai_usage.total_tokens > 0
    assert report.productivity.hours_saved > 0
    assert 0 <= report.risk.score <= 100
    assert len(report.pr_risks) == 8
    assert len(report.story_risks) == 5


def test_html_render_contains_key_sections():
    html = render_html(_report())
    assert "AI Dependency Risk" in html
    assert "KAN-20001" in html
    assert "Pull requests" in html
    assert "plotly" in html.lower()


def test_json_roundtrip(tmp_path: Path):
    report = _report()
    path = tmp_path / "out.json"
    save_report(report, path)
    loaded = load_report(path)
    assert loaded.epic.key == report.epic.key
    assert len(loaded.stories) == len(report.stories)
    assert loaded.risk.score == report.risk.score
