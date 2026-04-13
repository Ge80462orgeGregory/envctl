"""Flatten multiple environments into a single merged variable set."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


@dataclass
class FlattenError(Exception):
    message: str

    def __str__(self) -> str:
        return self.message


@dataclass
class FlattenResult:
    project: str
    environments: list[str]
    merged: dict[str, str]
    conflicts: dict[str, list[tuple[str, str]]]  # key -> [(env, value), ...]

    @property
    def total_keys(self) -> int:
        return len(self.merged)

    @property
    def total_conflicts(self) -> int:
        return len(self.conflicts)


def flatten_envs(
    project: str,
    environments: list[str],
    read_env: Callable[[str, str], dict[str, str]],
    list_environments: Callable[[str], list[str]],
    *,
    priority: str | None = None,
    skip_conflicts: bool = False,
) -> FlattenResult:
    """Merge variables from multiple environments into one dict.

    Args:
        project: Project name.
        environments: Ordered list of environments to merge (later wins).
        read_env: Callable(project, env) -> dict.
        list_environments: Callable(project) -> list[str].
        priority: If set, values from this env take precedence over merge order.
        skip_conflicts: If True, conflicting keys are omitted from merged output.
    """
    available = list_environments(project)
    if not available:
        raise FlattenError(f"Project '{project}' has no environments.")

    missing = [e for e in environments if e not in available]
    if missing:
        raise FlattenError(
            f"Environments not found in '{project}': {', '.join(missing)}"
        )

    if not environments:
        raise FlattenError("At least one environment must be specified.")

    # Collect per-key contributions
    contributions: dict[str, list[tuple[str, str]]] = {}
    for env in environments:
        data = read_env(project, env)
        for key, value in data.items():
            contributions.setdefault(key, []).append((env, value))

    merged: dict[str, str] = {}
    conflicts: dict[str, list[tuple[str, str]]] = {}

    for key, entries in contributions.items():
        values = [v for _, v in entries]
        unique_values = list(dict.fromkeys(values))

        if len(unique_values) > 1:
            conflicts[key] = entries
            if skip_conflicts:
                continue
            if priority and any(env == priority for env, _ in entries):
                merged[key] = next(v for env, v in entries if env == priority)
            else:
                # Last-writer wins
                merged[key] = entries[-1][1]
        else:
            merged[key] = unique_values[0]

    return FlattenResult(
        project=project,
        environments=environments,
        merged=merged,
        conflicts=conflicts,
    )
