"""Validation helpers for generated architecture output."""

from __future__ import annotations

import re

from ai_system_architect.core.exceptions import OutputValidationError

_SECTION_PATTERNS: tuple[tuple[int, str], ...] = (
    (0, r"^#+\s*(?:Section\s+)?0(?:\s*[—-]\s*|\.\s+|\s+)Assumptions\b"),
    (1, r"^#+\s*(?:Section\s+)?1(?:\s*[—-]\s*|\.\s+|\s+)Problem Statement\b"),
    (2, r"^#+\s*(?:Section\s+)?2(?:\s*[—-]\s*|\.\s+|\s+)Architecture Diagram\b"),
    (3, r"^#+\s*(?:Section\s+)?3(?:\s*[—-]\s*|\.\s+|\s+)LLM Recommendation\b"),
    (4, r"^#+\s*(?:Section\s+)?4(?:\s*[—-]\s*|\.\s+|\s+)Embedding Recommendation\b"),
    (5, r"^#+\s*(?:Section\s+)?5(?:\s*[—-]\s*|\.\s+|\s+)Vector Database\b"),
    (6, r"^#+\s*(?:Section\s+)?6(?:\s*[—-]\s*|\.\s+|\s+)Framework\b"),
    (7, r"^#+\s*(?:Section\s+)?7(?:\s*[—-]\s*|\.\s+|\s+)APIs\b"),
    (8, r"^#+\s*(?:Section\s+)?8(?:\s*[—-]\s*|\.\s+|\s+)Memory Strategy\b"),
    (9, r"^#+\s*(?:Section\s+)?9(?:\s*[—-]\s*|\.\s+|\s+)Deployment\b"),
    (10, r"^#+\s*(?:Section\s+)?10(?:\s*[—-]\s*|\.\s+|\s+)Evaluation\b"),
    (11, r"^#+\s*(?:Section\s+)?11(?:\s*[—-]\s*|\.\s+|\s+)Cost Estimate\b"),
    (12, r"^#+\s*(?:Section\s+)?12(?:\s*[—-]\s*|\.\s+|\s+)Risks\b"),
    (13, r"^#+\s*(?:Section\s+)?13(?:\s*[—-]\s*|\.\s+|\s+)Future Improvements\b"),
    (14, r"^#+\s*(?:Section\s+)?14(?:\s*[—-]\s*|\.\s+|\s+)Open Questions\b"),
)


def validate_architecture_markdown(markdown: str) -> str:
    """Ensure the model returned the required architecture contract."""
    text = markdown.strip()
    if not text:
        raise OutputValidationError("Generated markdown was empty.")

    missing: list[str] = []
    for section_number, pattern in _SECTION_PATTERNS:
        if re.search(pattern, text, flags=re.MULTILINE) is None:
            missing.append(str(section_number))

    if missing:
        raise OutputValidationError(
            "Generated markdown is missing required sections: " + ", ".join(missing)
        )

    if "```mermaid" not in text:
        raise OutputValidationError("Generated markdown is missing the Mermaid diagram block.")

    return text
