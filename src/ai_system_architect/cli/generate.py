"""Interactive architecture generation command."""

from __future__ import annotations

import typer
from rich.console import Console

from ai_system_architect.core.exceptions import ArchitectError
from ai_system_architect.services.architecture import generate_architecture

USE_CASE_PROMPT = "Describe your AI application."
GENERATING_MESSAGE = "Generating architecture..."


def run_generate_flow(
    console: Console,
    *,
    description: str | None = None,
) -> None:
    """Collect use case text, invoke the service layer, and show progress."""
    use_case = (description or typer.prompt(USE_CASE_PROMPT)).strip()
    if not use_case:
        console.print("[red]Description cannot be empty.[/red]")
        raise typer.Exit(code=1)

    try:
        console.print(GENERATING_MESSAGE)
        markdown = generate_architecture(use_case)
    except (ValueError, ArchitectError) as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    console.print(markdown, markup=False)
