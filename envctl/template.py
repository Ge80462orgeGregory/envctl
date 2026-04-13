"""Template rendering for environment variable sets.

Allows users to render a template string or file using variables
from a stored environment, substituting {{KEY}} placeholders.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable


class TemplateError(Exception):
    """Raised when template rendering fails."""


@dataclass
class TemplateResult:
    rendered: str
    substituted: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)

    @property
    def total_substituted(self) -> int:
        return len(self.substituted)

    @property
    def total_missing(self) -> int:
        return len(self.missing)


_PLACEHOLDER = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")


def render_template(
    template: str,
    read_env: Callable[[str, str], dict[str, str]],
    project: str,
    environment: str,
    *,
    strict: bool = False,
) -> TemplateResult:
    """Render *template* by substituting ``{{KEY}}`` placeholders.

    Parameters
    ----------
    template:
        The raw template string containing ``{{KEY}}`` placeholders.
    read_env:
        Callable matching ``env_store.read_env`` signature.
    project:
        Project name to look up variables from.
    environment:
        Environment name to look up variables from.
    strict:
        When *True*, raise :class:`TemplateError` if any placeholder
        has no matching key in the environment.
    """
    variables = read_env(project, environment)
    if not variables and strict:
        raise TemplateError(
            f"No variables found for '{project}/{environment}'."
        )

    substituted: list[str] = []
    missing: list[str] = []

    def _replace(match: re.Match) -> str:
        key = match.group(1)
        if key in variables:
            substituted.append(key)
            return variables[key]
        missing.append(key)
        return match.group(0)  # leave placeholder intact

    rendered = _PLACEHOLDER.sub(_replace, template)

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique_substituted = [k for k in substituted if not (k in seen or seen.add(k))]
    unique_missing = list(dict.fromkeys(missing))

    if strict and unique_missing:
        raise TemplateError(
            f"Missing keys in '{project}/{environment}': {', '.join(unique_missing)}"
        )

    return TemplateResult(
        rendered=rendered,
        substituted=unique_substituted,
        missing=unique_missing,
    )
