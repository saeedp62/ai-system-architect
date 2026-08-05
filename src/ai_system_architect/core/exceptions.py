"""Shared exception types for the application layer."""

from __future__ import annotations


class ArchitectError(Exception):
    """Base error for recoverable application failures."""


class ConfigurationError(ArchitectError):
    """Invalid or missing configuration."""


class LLMError(ArchitectError):
    """Upstream LLM provider failure or unexpected response."""
