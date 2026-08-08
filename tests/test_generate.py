"""Tests for generate flow and OpenAI Responses integration."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from openai import OpenAIError
from typer.testing import CliRunner

from ai_system_architect.cli.app import app
from ai_system_architect.config.settings import Settings
from ai_system_architect.core.exceptions import InsufficientInputError, OutputValidationError
from ai_system_architect.core.request import ArchitectureRequest
from ai_system_architect.services import architecture
from ai_system_architect.services.architecture import generate_architecture


class FakeResponses:
    def __init__(self, response: object | None = None, exc: Exception | None = None) -> None:
        self.response = response
        self.exc = exc
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.exc is not None:
            raise self.exc
        assert self.response is not None
        return self.response


class FakeClient:
    def __init__(self, responses: FakeResponses) -> None:
        self.responses = responses


def test_generate_architecture_returns_markdown(monkeypatch) -> None:
    settings = Settings(
        openai_api_key="sk-test",
        openai_base_url=None,
        openai_model="gpt-4o",
        log_level="INFO",
        output_dir=Path("/tmp"),
    )
    response = SimpleNamespace(
        output_text=(
            "### Section 0 — Assumptions\n\n- None\n\n"
            "### 1. Problem Statement\n\n- Example\n\n"
            "### 2. Architecture Diagram\n\n```mermaid\nflowchart LR\nA --> B\n```\n\n"
            "### 3. LLM Recommendation\n\n| Field | Value |\n|---|---|\n| Primary | gpt-4o |\n| Why | Test |\n| Confidence | High |\n| Rejected alternative | gpt-4o-mini |\n| Fallback | None |\n\n"
            "### 4. Embedding Recommendation\n\nNot required — example.\n\n"
            "### 5. Vector Database\n\nNot required — example.\n\n"
            "### 6. Framework\n\nnone — direct SDK calls.\n\n"
            "### 7. APIs\n\n| Interface | Method + path | Purpose | Auth | Sync/Async |\n|---|---|---|---|---|\n| API | POST /generate | Generate | None | Sync |\n\n"
            "### 8. Memory Strategy\n\n| Layer | Decision |\n|---|---|\n| Within-request context | none |\n| Cross-turn / session | none |\n| Long-term / user | none |\n| Caching | none |\n\n"
            "### 9. Deployment\n\n- Example\n\n"
            "### 10. Evaluation\n\n- Example\n\n"
            "### 11. Cost Estimate\n\n- Example\n\n"
            "### 12. Risks\n\n- Example\n\n"
            "### 13. Future Improvements\n\n- Example\n\n"
            "### 14. Open Questions\n\n- Example\n"
        ),
        error=None,
        incomplete_details=None,
    )
    responses = FakeResponses(response=response)
    client = FakeClient(responses)

    monkeypatch.setattr(architecture, "get_settings", lambda strict=True: settings)
    monkeypatch.setattr(architecture, "_create_client", lambda _: client)

    request = ArchitectureRequest.from_description("A chatbot for internal HR policies.")
    markdown = generate_architecture(request)

    assert markdown.startswith("### Section 0")
    assert responses.calls[0]["model"] == "gpt-4o"
    assert responses.calls[0]["input"] == request.to_prompt_text()
    assert responses.calls[0]["instructions"] == (
        Path("src/ai_system_architect/prompts/system_prompt.md").read_text(encoding="utf-8").strip()
    )
    assert responses.calls[0]["max_output_tokens"] == 5000
    assert responses.calls[0]["temperature"] == 0.2
    assert responses.calls[0]["store"] is False


def test_generate_architecture_rejects_blank() -> None:
    try:
        generate_architecture("   ")
    except ValueError as exc:
        assert "empty" in str(exc).lower()
    else:
        raise AssertionError("expected ValueError")


def test_generate_architecture_wraps_openai_errors(monkeypatch) -> None:
    settings = Settings(
        openai_api_key="sk-test",
        openai_base_url=None,
        openai_model="gpt-4o",
        log_level="INFO",
        output_dir=Path("/tmp"),
    )
    responses = FakeResponses(exc=OpenAIError("boom"))
    client = FakeClient(responses)

    monkeypatch.setattr(architecture, "get_settings", lambda strict=True: settings)
    monkeypatch.setattr(architecture, "_create_client", lambda _: client)

    try:
        generate_architecture(ArchitectureRequest.from_description("Invoice processing agent"))
    except architecture.LLMError as exc:
        assert "request failed" in str(exc).lower()
    else:
        raise AssertionError("expected LLMError")


def test_generate_architecture_rejects_invalid_output(monkeypatch) -> None:
    settings = Settings(
        openai_api_key="sk-test",
        openai_base_url=None,
        openai_model="gpt-4o",
        log_level="INFO",
        output_dir=Path("/tmp"),
    )
    response = SimpleNamespace(
        output_text="# Architecture\n\n- item",
        error=None,
        incomplete_details=None,
    )
    responses = FakeResponses(response=response)
    client = FakeClient(responses)

    monkeypatch.setattr(architecture, "get_settings", lambda strict=True: settings)
    monkeypatch.setattr(architecture, "_create_client", lambda _: client)

    try:
        generate_architecture(ArchitectureRequest.from_description("Invoice processing agent"))
    except OutputValidationError as exc:
        assert "missing required sections" in str(exc).lower()
    else:
        raise AssertionError("expected OutputValidationError")


def test_generate_architecture_raises_insufficient_input(monkeypatch) -> None:
    settings = Settings(
        openai_api_key="sk-test",
        openai_base_url=None,
        openai_model="gpt-4o",
        log_level="INFO",
        output_dir=Path("/tmp"),
    )
    response = SimpleNamespace(
        output_text=(
            "**Insufficient input.** I need the following before this would be useful rather than generic:\n"
            "1. Specific technologies or frameworks you prefer to use or want to avoid.\n"
            "2. Expected volume of queries or tickets per day.\n"
            "3. Any specific integrations required with existing systems."
        ),
        error=None,
        incomplete_details=None,
    )
    responses = FakeResponses(response=response)
    client = FakeClient(responses)

    monkeypatch.setattr(architecture, "get_settings", lambda strict=True: settings)
    monkeypatch.setattr(architecture, "_create_client", lambda _: client)

    try:
        generate_architecture(ArchitectureRequest.from_description("Invoice processing agent"))
    except InsufficientInputError as exc:
        assert exc.reasons == [
            "Specific technologies or frameworks you prefer to use or want to avoid.",
            "Expected volume of queries or tickets per day.",
            "Any specific integrations required with existing systems.",
        ]
    else:
        raise AssertionError("expected InsufficientInputError")


def test_cli_generate_with_description_flag(monkeypatch) -> None:
    runner = CliRunner()
    monkeypatch.setattr(
        "ai_system_architect.cli.generate.generate_architecture",
        lambda _description: "# Architecture\n\n- item",
    )

    result = runner.invoke(app, ["generate", "-d", "Invoice processing agent"])

    assert result.exit_code == 0
    assert "Request payload:" in result.output
    assert "deployment_target: Unsure" in result.output
    assert "Generating architecture..." in result.output
    assert "# Architecture" in result.output


def test_cli_proceeds_after_insufficient_input_confirmation(monkeypatch) -> None:
    runner = CliRunner()
    calls: list[bool] = []

    def fake_generate_architecture(request, *, proceed_anyway: bool = False):
        calls.append(proceed_anyway)
        if not proceed_anyway:
            raise InsufficientInputError(
                "Insufficient input",
                reasons=["Need more context."],
                raw_output="**Insufficient input.** Need more context.",
            )
        return "# Architecture\n\n- item"

    monkeypatch.setattr(
        "ai_system_architect.cli.generate.generate_architecture",
        fake_generate_architecture,
    )

    result = runner.invoke(
        app,
        ["generate", "-d", "Invoice processing agent"],
        input="y\n",
    )

    assert result.exit_code == 0
    assert "The model said the input was insufficient." in result.output
    assert "Need more context." in result.output
    assert "Retrying with proceed-anyway override..." in result.output
    assert calls == [False, True]
    assert "# Architecture" in result.output


def test_cli_default_invokes_generate_prompt(monkeypatch) -> None:
    runner = CliRunner()
    monkeypatch.setattr(
        "ai_system_architect.cli.generate.generate_architecture",
        lambda _description: "# Architecture\n\n- item",
    )

    result = runner.invoke(app, input="Customer support copilot\n")

    assert result.exit_code == 0
    assert "Describe your AI application." in result.output
    assert "Generating architecture..." in result.output
    assert "# Architecture" in result.output
