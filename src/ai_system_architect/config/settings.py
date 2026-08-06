"""Environment-backed application settings."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import load_dotenv

from ai_system_architect.core.exceptions import ConfigurationError

_ENV_LOADED = False


def _ensure_dotenv() -> None:
    global _ENV_LOADED
    if not _ENV_LOADED:
        load_dotenv()
        _ENV_LOADED = True


def _require(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ConfigurationError(f"Missing required environment variable: {name}")
    return value


def _optional(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _normalize_base_url(raw_value: str) -> str | None:
    """Accept either a full URL or a bare host and return a usable base URL."""
    value = raw_value.strip()
    if not value:
        return None

    parsed = urlsplit(value)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return value.rstrip("/")

    if " " in value:
        raise ConfigurationError(
            "OPENAI_BASE_URL must be a URL like https://api.openai.com/v1."
        )

    if "://" not in value:
        return f"https://{value.rstrip('/')}"

    raise ConfigurationError(
        "OPENAI_BASE_URL must include http:// or https://, for example "
        "https://api.openai.com/v1."
    )


@dataclass(frozen=True, slots=True)
class Settings:
    """Immutable runtime configuration loaded from the environment."""

    openai_api_key: str
    openai_base_url: str | None
    openai_model: str
    log_level: str
    output_dir: Path

    @classmethod
    def from_env(cls) -> Settings:
        _ensure_dotenv()
        base_url = _normalize_base_url(_optional("OPENAI_BASE_URL"))
        output_dir = Path(_optional("OUTPUT_DIR", "./outputs")).expanduser().resolve()
        return cls(
            openai_api_key=_require("OPENAI_API_KEY"),
            openai_base_url=base_url,
            openai_model=_optional("OPENAI_MODEL", "gpt-4o-mini"),
            log_level=_optional("LOG_LEVEL", "INFO").upper(),
            output_dir=output_dir,
        )


def get_settings(*, strict: bool = True) -> Settings:
    """Load settings. When ``strict`` is False, missing keys are tolerated for health checks."""
    if strict:
        return Settings.from_env()
    _ensure_dotenv()
    return Settings(
        openai_api_key=_optional("OPENAI_API_KEY"),
        openai_base_url=_normalize_base_url(_optional("OPENAI_BASE_URL")),
        openai_model=_optional("OPENAI_MODEL", "gpt-4o-mini"),
        log_level=_optional("LOG_LEVEL", "INFO").upper(),
        output_dir=Path(_optional("OUTPUT_DIR", "./outputs")).expanduser().resolve(),
    )
