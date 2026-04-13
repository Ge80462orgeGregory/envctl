"""Reorder keys in an environment alphabetically or by a custom key list."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


class ReorderError(Exception):
    """Raised when reordering fails."""


@dataclass
class ReorderResult:
    project: str
    environment: str
    original_order: List[str] = field(default_factory=list)
    new_order: List[str] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return self.original_order != self.new_order

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "environment": self.environment,
            "original_order": self.original_order,
            "new_order": self.new_order,
            "changed": self.changed,
        }


def reorder_env(
    project: str,
    environment: str,
    *,
    read_env: Callable[[str, str], Dict[str, str]],
    write_env: Callable[[str, str, Dict[str, str]], None],
    key_order: Optional[List[str]] = None,
    reverse: bool = False,
) -> ReorderResult:
    """Reorder keys in an environment.

    If *key_order* is provided, keys are placed in that order first;
    any remaining keys are appended alphabetically.
    If *key_order* is None, all keys are sorted alphabetically.
    """
    env = read_env(project, environment)
    if not env:
        raise ReorderError(
            f"Environment '{environment}' in project '{project}' is empty or does not exist."
        )

    original_order = list(env.keys())

    if key_order is not None:
        unknown = [k for k in key_order if k not in env]
        if unknown:
            raise ReorderError(
                f"Keys not found in environment: {', '.join(unknown)}"
            )
        remaining = sorted(
            (k for k in env if k not in key_order), reverse=reverse
        )
        ordered_keys = key_order + remaining
    else:
        ordered_keys = sorted(env.keys(), reverse=reverse)

    reordered: Dict[str, str] = {k: env[k] for k in ordered_keys}
    write_env(project, environment, reordered)

    return ReorderResult(
        project=project,
        environment=environment,
        original_order=original_order,
        new_order=ordered_keys,
    )
