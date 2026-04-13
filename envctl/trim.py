"""Trim unused or duplicate keys from an environment."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


class TrimError(Exception):
    """Raised when a trim operation fails."""


@dataclass
class TrimResult:
    removed: list[str] = field(default_factory=list)
    kept: list[str] = field(default_factory=list)

    @property
    def total_removed(self) -> int:
        return len(self.removed)


def trim_env(
    project: str,
    environment: str,
    *,
    keys: list[str] | None = None,
    dry_run: bool = False,
    read_env: Callable[[str, str], dict[str, str]],
    write_env: Callable[[str, str, dict[str, str]], None],
) -> TrimResult:
    """Remove specified keys (or empty-valued keys) from an environment.

    If *keys* is provided, only those keys are candidates for removal.
    Otherwise every key whose value is an empty string is removed.

    When *dry_run* is ``True`` the store is not mutated.
    """
    current = read_env(project, environment)
    if not current:
        raise TrimError(
            f"Environment '{environment}' for project '{project}' does not exist or is empty."
        )

    result = TrimResult()

    if keys is not None:
        missing = [k for k in keys if k not in current]
        if missing:
            raise TrimError(
                f"Keys not found in '{project}/{environment}': {', '.join(missing)}"
            )
        candidates = set(keys)
    else:
        candidates = {k for k, v in current.items() if v == ""}

    updated: dict[str, str] = {}
    for k, v in current.items():
        if k in candidates:
            result.removed.append(k)
        else:
            result.kept.append(k)
            updated[k] = v

    if not dry_run and result.removed:
        write_env(project, environment, updated)

    return result
