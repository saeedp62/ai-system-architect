"""Typer CLI application."""

from __future__ import annotations

import logging
from typing import Annotated

import typer
from rich.console import Console

from ai_system_architect import __version__
from ai_system_architect.config.settings import get_settings
from ai_system_architect.core.exceptions import ConfigurationError
from ai_system_architect.core.logging import setup_logging

app = typer.Typer(
    name="architect",
    help="AI System Architect — draft architectures from use case descriptions.",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()
logger = logging.getLogger(__name__)


@app.callback()
def main(
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Enable debug logging."),
    ] = False,
) -> None:
    """Global options applied before subcommands."""
    if verbose:
        import os

        os.environ["LOG_LEVEL"] = "DEBUG"
    settings = get_settings(strict=False)
    setup_logging(settings)


@app.command("version")
def version_cmd() -> None:
    """Print package version."""
    console.print(f"ai-system-architect {__version__}")


@app.command("doctor")
def doctor_cmd() -> None:
    """Verify configuration and provider connectivity (stub)."""
    try:
        settings = get_settings(strict=True)
    except ConfigurationError as exc:
        console.print(f"[red]Configuration error:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    setup_logging(settings)
    console.print("[green]Configuration loaded.[/green]")
    console.print(f"  Model: [cyan]{settings.openai_model}[/cyan]")
    console.print(f"  Output dir: [cyan]{settings.output_dir}[/cyan]")
    console.print("[dim]Generation and API ping will be added in a later milestone.[/dim]")
