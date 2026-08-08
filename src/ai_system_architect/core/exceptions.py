"""Shared exception types for the application layer."""

from __future__ import annotations


class ArchitectError(Exception):
    """Base error for recoverable application failures."""


class ConfigurationError(ArchitectError):
    """Invalid or missing configuration."""


class LLMError(ArchitectError):
    """Upstream LLM provider failure or unexpected response."""


class OutputValidationError(ArchitectError):
    """Generated markdown did not satisfy the expected contract."""


class InsufficientInputError(ArchitectError):
    """The model asked for more input before it could generate an architecture."""

    def __init__(self, message: str, reasons: list[str], raw_output: str) -> None:
        super().__init__(message)
        self.reasons = reasons
        self.raw_output = raw_output
