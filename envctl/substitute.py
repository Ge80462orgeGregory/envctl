"""Substitute: replace literal values in an env with values from another env."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, Optional


class SubstituteError(Exception):
    """Raised when substitution cannot be completed."""


@dataclass
class SubstituteResult:
    project: str
    environment: str
    substituted: Dict[str, str] = field(default_factory=dict)  # key -> new_value
    skipped: Dict[str, str] = field(default_factory=dict)      # key -> reason

    @property
    def total_substituted(self) -> int:
        return len(self.substituted)

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "environment": self.environment,
            "total_substituted": self.total_substituted,
            "substituted": self.substituted,
            "skipped": self.skipped,
        }


def substitute_env(
    project: str,
    environment: str,
    source_values: Dict[str, str],
    read_env: Callable[[str, str], Dict[str, str]],
    write_env: Callable[[str, str, Dict[str, str]], None],
    keys: Optional[list] = None,
    overwrite: bool = True,
) -> SubstituteResult:
    """Replace values in *environment* with those from *source_values*.

    Only keys that already exist in the target environment are eligible for
    substitution unless *keys* is explicitly provided.

    Args:
        project: target project name.
        environment: target environment name.
        source_values: mapping of key -> replacement value.
        read_env: callable to read an environment's variables.
        write_env: callable to persist updated variables.
        keys: optional explicit list of keys to substitute; defaults to all
              keys present in both target and source.
        overwrite: when False, skip keys that already have a non-empty value.
    """
    if not project:
        raise SubstituteError("project must not be empty")
    if not environment:
        raise SubstituteError("environment must not be empty")
    if not source_values:
        raise SubstituteError("source_values must not be empty")

    target = read_env(project, environment)
    result = SubstituteResult(project=project, environment=environment)

    candidates = keys if keys is not None else list(target.keys())

    updated = dict(target)
    for key in candidates:
        if key not in source_values:
            result.skipped[key] = "not in source"
            continue
        if key not in target:
            result.skipped[key] = "not in target"
            continue
        if not overwrite and target.get(key, ""):
            result.skipped[key] = "already has value"
            continue
        updated[key] = source_values[key]
        result.substituted[key] = source_values[key]

    write_env(project, environment, updated)
    return result
