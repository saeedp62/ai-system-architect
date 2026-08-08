"""Interactive architecture generation command."""

from __future__ import annotations

import typer
from rich.console import Console

from ai_system_architect.core.exceptions import ArchitectError, InsufficientInputError
from ai_system_architect.core.request import (
    ArchitectureRequest,
    DataSensitivity,
    DeploymentTarget,
    Scale,
)
from ai_system_architect.services.architecture import generate_architecture

USE_CASE_PROMPT = "Describe your AI application."
GENERATING_MESSAGE = "Generating architecture..."


def run_generate_flow(
    console: Console,
    *,
    description: str | None = None,
    deployment_target: DeploymentTarget | None = None,
    data_sensitivity: DataSensitivity | None = None,
    scale: Scale | None = None,
    approved_stack: list[str] | None = None,
) -> None:
    """Collect use case text, invoke the service layer, and show progress."""
    use_case = (description or typer.prompt(USE_CASE_PROMPT)).strip()
    if not use_case:
        console.print("[red]Description cannot be empty.[/red]")
        raise typer.Exit(code=1)

    request = ArchitectureRequest(
        description=use_case,
        deployment_target=deployment_target or DeploymentTarget.UNSURE,
        data_sensitivity=data_sensitivity or DataSensitivity.UNSURE,
        scale=scale or Scale.UNSURE,
        approved_stack=tuple(approved_stack or ()),
    )

    try:
        console.print("[bold]Request payload:[/bold]")
        console.print(request.to_prompt_text(), markup=False)
        console.print(GENERATING_MESSAGE)
        markdown = generate_architecture(request)
    except InsufficientInputError as exc:
        console.print("[yellow]The model said the input was insufficient.[/yellow]")
        if exc.reasons:
            console.print("[bold]Why it wanted more input:[/bold]")
            for reason in exc.reasons:
                console.print(f"- {reason}")
        else:
            console.print(exc.raw_output, markup=False)

        if not typer.confirm("Proceed anyway with stated assumptions?", default=False):
            raise typer.Exit(code=1)

        try:
            console.print("[bold]Retrying with proceed-anyway override...[/bold]")
            console.print(request.to_prompt_text(proceed_anyway=True), markup=False)
            markdown = generate_architecture(request, proceed_anyway=True)
        except (ValueError, ArchitectError) as retry_exc:
            console.print(f"[red]{retry_exc}[/red]")
            raise typer.Exit(code=1) from retry_exc
    except (ValueError, ArchitectError) as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    console.print(markdown, markup=False)
