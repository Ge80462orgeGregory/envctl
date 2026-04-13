"""Detect and report unresolved placeholder variables in an environment."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable

# Matches ${VAR_NAME} or $VAR_NAME style placeholders inside values
_PLACEHOLDER_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\$([A-Za-z_][A-Za-z0-9_]*)")


class PlaceholderError(Exception):
    """Raised when placeholder detection cannot proceed."""


@dataclass
class PlaceholderMatch:
    key: str
    value: str
    placeholders: list[str]

    def to_dict(self) -> dict:
        return {"key": self.key, "value": self.value, "placeholders": self.placeholders}


@dataclass
class PlaceholderResult:
    project: str
    environment: str
    matches: list[PlaceholderMatch] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.matches)

    @property
    def has_unresolved(self) -> bool:
        return len(self.matches) > 0

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "environment": self.environment,
            "total": self.total,
            "matches": [m.to_dict() for m in self.matches],
        }


def find_placeholders(
    project: str,
    environment: str,
    read_env: Callable[[str, str], dict[str, str]],
) -> PlaceholderResult:
    """Scan an environment's values for unresolved placeholder references."""
    env = read_env(project, environment)
    if env is None:
        raise PlaceholderError(f"Environment '{environment}' not found in project '{project}'.")

    result = PlaceholderResult(project=project, environment=environment)

    for key, value in env.items():
        found = _PLACEHOLDER_RE.findall(value)
        # findall returns list of tuples (group1, group2)
        names = [g1 or g2 for g1, g2 in found if (g1 or g2)]
        if names:
            result.matches.append(PlaceholderMatch(key=key, value=value, placeholders=names))

    return result
