"""Structured request objects for architecture generation."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class DeploymentTarget(StrEnum):
    """Deployment location constraints supplied by the user."""

    CLOUD = "Cloud"
    ON_PREM = "On-prem"
    HYBRID = "Hybrid"
    UNSURE = "Unsure"


class DataSensitivity(StrEnum):
    """Data handling sensitivity supplied by the user."""

    PUBLIC = "Public"
    INTERNAL = "Internal"
    REGULATED = "Regulated"
    UNSURE = "Unsure"


class Scale(StrEnum):
    """Operating scale supplied by the user."""

    PROTOTYPE = "Prototype"
    TEAM = "Team"
    ENTERPRISE = "Enterprise"
    UNSURE = "Unsure"


@dataclass(frozen=True, slots=True)
class ArchitectureRequest:
    """Normalized input for the architecture generator."""

    description: str
    deployment_target: DeploymentTarget = DeploymentTarget.UNSURE
    data_sensitivity: DataSensitivity = DataSensitivity.UNSURE
    scale: Scale = Scale.UNSURE
    approved_stack: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        description = self.description.strip()
        approved_stack = tuple(item.strip() for item in self.approved_stack if item.strip())
        object.__setattr__(self, "description", description)
        object.__setattr__(self, "approved_stack", approved_stack)

    @classmethod
    def from_description(cls, description: str) -> ArchitectureRequest:
        """Build a request from the current CLI input shape."""
        return cls(description=description)

    def to_prompt_text(self, *, proceed_anyway: bool = False) -> str:
        """Serialize the structured request into a deterministic prompt payload."""
        lines = [
            "Use case description:",
            self.description,
            "",
            "Constraints:",
            f"- deployment_target: {self.deployment_target.value}",
            f"- data_sensitivity: {self.data_sensitivity.value}",
            f"- scale: {self.scale.value}",
            "- approved_stack: "
            + (", ".join(self.approved_stack) if self.approved_stack else "none"),
        ]
        if proceed_anyway:
            lines.extend(
                [
                    "",
                    "User confirmation:",
                    "Proceed anyway and produce the best possible 15-section architecture using explicit assumptions.",
                ]
            )
        return "\n".join(lines).strip()
