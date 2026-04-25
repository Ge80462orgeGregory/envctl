"""omit.py — Remove specific keys from an environment, writing the result back."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List


class OmitError(Exception):
    """Raised when omit_env encounters a problem."""


@dataclass
class OmitResult:
    project: str
    environment: str
    removed: List[str] = field(default_factory=list)
    not_found: List[str] = field(default_factory=list)

    @property
    def total_removed(self) -> int:
        return len(self.removed)

    def to_dict(self) -> Dict:
        return {
            "project": self.project,
            "environment": self.environment,
            "removed": self.removed,
            "not_found": self.not_found,
            "total_removed": self.total_removed,
        }


def omit_env(
    project: str,
    environment: str,
    keys: List[str],
    read_env: Callable[[str, str], Dict[str, str]],
    write_env: Callable[[str, str, Dict[str, str]], None],
) -> OmitResult:
    """Remove *keys* from *project*/*environment*.

    Args:
        project:     Project name.
        environment: Environment name.
        keys:        Keys to remove.
        read_env:    Callable(project, env) -> dict.
        write_env:   Callable(project, env, dict) -> None.

    Returns:
        OmitResult describing what was removed and what was missing.

    Raises:
        OmitError: If *keys* is empty.
    """
    if not keys:
        raise OmitError("At least one key must be specified for omit.")

    current = read_env(project, environment)
    result = OmitResult(project=project, environment=environment)

    updated = dict(current)
    for key in keys:
        if key in updated:
            del updated[key]
            result.removed.append(key)
        else:
            result.not_found.append(key)

    write_env(project, environment, updated)
    return result
