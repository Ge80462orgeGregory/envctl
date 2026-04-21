"""Touch — ensure keys exist in an environment, setting them to a default value if missing."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List


class TouchError(Exception):
    """Raised when touch_env fails."""


@dataclass
class TouchResult:
    project: str
    environment: str
    added: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    @property
    def total_added(self) -> int:
        return len(self.added)

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "environment": self.environment,
            "added": self.added,
            "skipped": self.skipped,
            "total_added": self.total_added,
        }


def touch_env(
    project: str,
    environment: str,
    keys: List[str],
    default: str = "",
    read: Callable[[str, str], Dict[str, str]] = None,
    write: Callable[[str, str, Dict[str, str]], None] = None,
) -> TouchResult:
    """Ensure *keys* exist in the environment.  Missing keys are created with
    *default*; keys that already exist are left unchanged."""

    if read is None or write is None:
        raise TouchError("read and write callables are required")

    if not keys:
        raise TouchError("at least one key must be specified")

    current = read(project, environment)
    result = TouchResult(project=project, environment=environment)

    updated = dict(current)
    for key in keys:
        if not key:
            raise TouchError("key must not be empty")
        if key in current:
            result.skipped.append(key)
        else:
            updated[key] = default
            result.added.append(key)

    if result.added:
        write(project, environment, updated)

    return result
