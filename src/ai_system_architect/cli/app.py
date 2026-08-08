"""Typer CLI application."""

from __future__ import annotations

import logging
from typing import Annotated

import typer
from rich.console import Console

from ai_system_architect import __version__
from ai_system_architect.cli.generate import run_generate_flow
from ai_system_architect.config.settings import get_settings
from ai_system_architect.core.exceptions import ConfigurationError
from ai_system_architect.core.request import DataSensitivity, DeploymentTarget, Scale
from ai_system_architect.core.logging import setup_logging

app = typer.Typer(
    name="architect",
    help="AI System Architect — draft architectures from use case descriptions.",
    invoke_without_command=True,
    no_args_is_help=False,
    add_completion=False,
)
console = Console()
logger = logging.getLogger(__name__)


@app.callback()
def main(
    ctx: typer.Context,
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

    if ctx.invoked_subcommand is None:
        run_generate_flow(console)


@app.command("generate")
def generate_cmd(
    description: Annotated[
        str | None,
        typer.Option(
            "--description",
            "-d",
            help="Use case text (skips interactive prompt when set).",
        ),
    ] = None,
    deployment_target: Annotated[
        DeploymentTarget | None,
        typer.Option(
            "--deployment-target",
            help="Deployment constraint for the architecture draft.",
        ),
    ] = None,
    data_sensitivity: Annotated[
        DataSensitivity | None,
        typer.Option(
            "--data-sensitivity",
            help="Data sensitivity constraint for the architecture draft.",
        ),
    ] = None,
    scale: Annotated[
        Scale | None,
        typer.Option(
            "--scale",
            help="Expected operating scale for the architecture draft.",
        ),
    ] = None,
    approved_stack: Annotated[
        list[str] | None,
        typer.Option(
            "--approved-stack",
            help="Technology name to constrain recommendations. Repeat the flag for multiple items.",
        ),
    ] = None,
) -> None:
    """Describe your application and start architecture generation."""
    run_generate_flow(
        console,
        description=description,
        deployment_target=deployment_target,
        data_sensitivity=data_sensitivity,
        scale=scale,
        approved_stack=approved_stack,
    )


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
