"""Set and apply default values for missing keys in an environment."""

from dataclasses import dataclass, field
from typing import Callable


class DefaultsError(Exception):
    pass


@dataclass
class DefaultsResult:
    project: str
    environment: str
    applied: dict[str, str] = field(default_factory=dict)
    skipped: list[str] = field(default_factory=list)

    @property
    def total_applied(self) -> int:
        return len(self.applied)

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "environment": self.environment,
            "applied": self.applied,
            "skipped": self.skipped,
            "total_applied": self.total_applied,
        }


def apply_defaults(
    project: str,
    environment: str,
    defaults: dict[str, str],
    read_env: Callable[[str, str], dict[str, str]],
    write_env: Callable[[str, str, dict[str, str]], None],
    overwrite: bool = False,
) -> DefaultsResult:
    """Apply default key/value pairs to an environment for any keys not already set."""
    if not project:
        raise DefaultsError("project must not be empty")
    if not environment:
        raise DefaultsError("environment must not be empty")
    if not defaults:
        raise DefaultsError("defaults must not be empty")

    current = read_env(project, environment)
    result = DefaultsResult(project=project, environment=environment)

    updated = dict(current)
    for key, value in defaults.items():
        if key in current and not overwrite:
            result.skipped.append(key)
        else:
            updated[key] = value
            result.applied[key] = value

    if result.applied:
        write_env(project, environment, updated)

    return result
