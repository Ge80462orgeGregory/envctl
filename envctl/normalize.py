"""Normalize environment variable keys and values in an env store."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


class NormalizeError(Exception):
    """Raised when normalization cannot be completed."""


@dataclass
class NormalizeResult:
    project: str
    environment: str
    renamed: dict[str, str] = field(default_factory=dict)   # old_key -> new_key
    trimmed: list[str] = field(default_factory=list)         # keys whose values were stripped
    skipped: list[str] = field(default_factory=list)         # keys left unchanged

    @property
    def total_changes(self) -> int:
        return len(self.renamed) + len(self.trimmed)

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "environment": self.environment,
            "renamed": self.renamed,
            "trimmed": self.trimmed,
            "skipped": self.skipped,
            "total_changes": self.total_changes,
        }


def _default_key_transform(key: str) -> str:
    """Upper-case and strip whitespace from a key."""
    return key.strip().upper()


def normalize_env(
    project: str,
    environment: str,
    read: Callable[[str, str], dict[str, str]],
    write: Callable[[str, str, dict[str, str]], None],
    *,
    key_transform: Callable[[str], str] | None = None,
    strip_values: bool = True,
) -> NormalizeResult:
    """Normalize keys and values for a given project/environment.

    Args:
        project: Project name.
        environment: Environment name.
        read: Callable(project, environment) -> dict of variables.
        write: Callable(project, environment, variables) -> None.
        key_transform: Optional function to transform each key.
            Defaults to upper-casing and stripping whitespace.
        strip_values: If True, strip leading/trailing whitespace from values.

    Returns:
        NormalizeResult describing what changed.

    Raises:
        NormalizeError: If the environment cannot be read or written.
    """
    transform = key_transform or _default_key_transform

    try:
        variables = read(project, environment)
    except Exception as exc:
        raise NormalizeError(f"Failed to read '{project}/{environment}': {exc}") from exc

    result = NormalizeResult(project=project, environment=environment)
    normalised: dict[str, str] = {}

    for key, value in variables.items():
        new_key = transform(key)
        new_value = value.strip() if strip_values else value

        if new_key != key:
            result.renamed[key] = new_key
        if new_value != value:
            result.trimmed.append(new_key)
        if new_key == key and new_value == value:
            result.skipped.append(key)

        normalised[new_key] = new_value

    try:
        write(project, environment, normalised)
    except Exception as exc:
        raise NormalizeError(f"Failed to write '{project}/{environment}': {exc}") from exc

    return result
