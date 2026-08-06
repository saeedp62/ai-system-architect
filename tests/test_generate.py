"""Tests for generate flow and OpenAI Responses integration."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from openai import OpenAIError
from typer.testing import CliRunner

from ai_system_architect.cli.app import app
from ai_system_architect.config.settings import Settings
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
        output_text="# Architecture\n\n- item",
        error=None,
        incomplete_details=None,
    )
    responses = FakeResponses(response=response)
    client = FakeClient(responses)

    monkeypatch.setattr(architecture, "get_settings", lambda strict=True: settings)
    monkeypatch.setattr(architecture, "_create_client", lambda _: client)

    markdown = generate_architecture("A chatbot for internal HR policies.")

    assert markdown == "# Architecture\n\n- item"
    assert responses.calls[0]["model"] == "gpt-4o"
    assert responses.calls[0]["input"] == "A chatbot for internal HR policies."
    assert responses.calls[0]["instructions"] == (
        Path("src/ai_system_architect/prompts/system_prompt.md").read_text(encoding="utf-8").strip()
    )
    assert responses.calls[0]["max_output_tokens"] == 1400
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
        generate_architecture("Invoice processing agent")
    except architecture.LLMError as exc:
        assert "request failed" in str(exc).lower()
    else:
        raise AssertionError("expected LLMError")


def test_cli_generate_with_description_flag(monkeypatch) -> None:
    runner = CliRunner()
    monkeypatch.setattr(
        "ai_system_architect.cli.generate.generate_architecture",
        lambda _description: "# Architecture\n\n- item",
    )

    result = runner.invoke(app, ["generate", "-d", "Invoice processing agent"])

    assert result.exit_code == 0
    assert "Generating architecture..." in result.output
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
