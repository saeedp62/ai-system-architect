"""Smoke tests for project scaffolding."""

from ai_system_architect import __version__
from ai_system_architect.config.settings import Settings


def test_version() -> None:
    assert __version__ == "0.1.0"


def test_settings_from_env(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o")
    settings = Settings.from_env()
    assert settings.openai_api_key == "sk-test"
    assert settings.openai_model == "gpt-4o"


def test_settings_normalizes_base_url(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("OPENAI_BASE_URL", "api.openai.com/v1")
    settings = Settings.from_env()
    assert settings.openai_base_url == "https://api.openai.com/v1"
