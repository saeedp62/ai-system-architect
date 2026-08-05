"""OpenAI client factory — no prompts or generation logic yet."""

from __future__ import annotations

import logging
from functools import lru_cache

from openai import OpenAI

from ai_system_architect.config.settings import Settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_openai_client(settings: Settings) -> OpenAI:
    """Return a cached OpenAI client for the given settings snapshot."""
    kwargs: dict[str, str] = {"api_key": settings.openai_api_key}
    if settings.openai_base_url:
        kwargs["base_url"] = settings.openai_base_url
    logger.debug("Initializing OpenAI client (model default: %s)", settings.openai_model)
    return OpenAI(**kwargs)
