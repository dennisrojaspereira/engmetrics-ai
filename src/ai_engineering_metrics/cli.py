"""Command-line interface (Typer).

The CLI is a thin shell over :class:`AnalysisService`: it parses options, builds
configuration, runs the analysis and writes the chosen output. All real work
lives in the service/domain layers so the same logic can back a web API later.
"""

from __future__ import annotations

import logging
from enum import StrEnum
from pathlib import Path

import typer

from ai_engineering_metrics import __version__
from ai_engineering_metrics.config import GitHubConfig, Settings
from ai_engineering_metrics.integrations.base import IntegrationError, NotFoundError
from ai_engineering_metrics.reports.html_report import write_html
from ai_engineering_metrics.service import AnalysisService
from ai_engineering_metrics.storage.json_storage import report_to_json, save_report

app = typer.Typer(
    add_completion=False,
    help="Measure the impact of AI usage on engineering delivery.",
    no_args_is_help=True,
)


class OutputFormat(StrEnum):
    html = "html"
    json = "json"


def _configure_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(levelname)s %(message)s",
    )


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"ai-engineering-metrics {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    _version: bool = typer.Option(
        False, "--version", callback=_version_callback, is_eager=True, help="Show version and exit."
    ),
) -> None:
    """ai-engineering-metrics CLI."""


@app.command()
def analyze(
    epic: str = typer.Option(..., "--epic", "-e", help="JIRA epic key, e.g. KAN-20001."),
    output: Path | None = typer.Option(
        None, "--output", "-o", help="Output file path. Defaults to ./reports/<EPIC>.<ext>."
    ),
    fmt: OutputFormat = typer.Option(
        OutputFormat.html, "--format", "-f", help="Output format: html or json."
    ),
    repo: str | None = typer.Option(
        None,
        "--repo",
        "-r",
        help="GitHub 'owner/name' to search for PRs. Overrides .env and auto-detection. "
        "When omitted, the repo is taken from .env or auto-detected from the current git remote.",
    ),
    mock: bool = typer.Option(
        False, "--mock", help="Run with realistic fake data (no JIRA/GitHub calls)."
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose logging."),
) -> None:
    """Analyze an epic and generate a dashboard (HTML) or a JSON report."""
    _configure_logging(verbose)

    settings = Settings.from_env()
    if repo:
        if "/" not in repo:
            typer.secho("--repo must be in 'owner/name' format.", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=2)
        owner, name = repo.split("/", 1)
        settings.github = GitHubConfig(org=owner, repositories=[name], search_all_repos=False)

    output_path = output or Path("reports") / f"{epic}.{fmt.value}"

    service: AnalysisService | None = None
    try:
        service = AnalysisService.for_settings(settings, mock=mock)
        report = service.analyze(epic)
    except NotFoundError as exc:
        typer.secho(f"Not found: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2) from exc
    except IntegrationError as exc:
        typer.secho(f"Integration error: {exc}", fg=typer.colors.RED, err=True)
        typer.secho("Tip: run with --mock to try the tool without credentials.", err=True)
        raise typer.Exit(code=1) from exc
    finally:
        if service is not None:
            service.close()

    if fmt is OutputFormat.json:
        if output is None:
            # No explicit path -> print JSON to stdout for piping.
            typer.echo(report_to_json(report))
            return
        saved = save_report(report, output_path)
        typer.secho(f"JSON report written to {saved}", fg=typer.colors.GREEN)
        return

    saved = write_html(report, output_path)
    typer.secho(f"Dashboard written to {saved}", fg=typer.colors.GREEN)
    typer.echo(
        f"  Epic {report.epic.key}: {len(report.stories)} stories, "
        f"{len(report.all_pull_requests)} PRs, "
        f"risk {report.risk.score} ({report.risk.level})."
    )


if __name__ == "__main__":
    app()
