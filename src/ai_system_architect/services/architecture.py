"""Architecture generation use case backed by the OpenAI Responses API."""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path

from openai import OpenAI, OpenAIError

from ai_system_architect.config.settings import Settings, get_settings
from ai_system_architect.core.exceptions import LLMError
from ai_system_architect.llm.client import get_openai_client

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "system_prompt.md"
_MAX_OUTPUT_TOKENS = 5000
_TEMPERATURE = 0.2


@lru_cache(maxsize=1)
def _load_system_prompt() -> str:
    """Load and cache the prompt used to steer architecture generation."""
    return _SYSTEM_PROMPT_PATH.read_text(encoding="utf-8").strip()


def _create_client(settings: Settings) -> OpenAI:
    """Create or reuse an OpenAI client for the current settings snapshot."""
    return get_openai_client(settings)


def generate_architecture(user_input: str) -> str:
    """Generate a markdown architecture draft for the provided use case."""
    description = user_input.strip()
    if not description:
        raise ValueError("Use case description must not be empty.")

    settings = get_settings(strict=True)
    client = _create_client(settings)
    system_prompt = _load_system_prompt()

    logger.debug(
        "Generating architecture with model=%s and %d characters of input",
        settings.openai_model,
        len(description),
    )

    try:
        response = client.responses.create(
            model=settings.openai_model,
            instructions=system_prompt,
            input=description,
            max_output_tokens=_MAX_OUTPUT_TOKENS,
            temperature=_TEMPERATURE,
            store=False,
        )
    except OpenAIError as exc:
        logger.exception("OpenAI Responses API call failed")
        error_message = f"OpenAI Responses API request failed: {exc}"
        raise LLMError(error_message) from exc

    if response.error is not None:
        logger.error("OpenAI returned an error response: %s", response.error)
        raise LLMError(f"OpenAI returned an error response: {response.error}")

    if response.incomplete_details is not None:
        logger.error("OpenAI response was incomplete: %s", response.incomplete_details)
        raise LLMError("OpenAI response was incomplete.")

    markdown = response.output_text.strip()
    if not markdown:
        logger.error("OpenAI response contained no markdown output")
        raise LLMError("OpenAI response contained no markdown output.")

    return markdown
