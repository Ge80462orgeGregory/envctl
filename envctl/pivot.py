"""Pivot: transpose an env's key-value pairs into a cross-environment comparison table."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


class PivotError(Exception):
    """Raised when pivot_env fails."""


@dataclass
class PivotRow:
    key: str
    values: Dict[str, Optional[str]]  # env_name -> value

    def to_dict(self) -> dict:
        return {"key": self.key, "values": self.values}


@dataclass
class PivotResult:
    project: str
    environments: List[str]
    rows: List[PivotRow] = field(default_factory=list)

    @property
    def total_keys(self) -> int:
        return len(self.rows)

    @property
    def total_missing(self) -> int:
        """Count of (key, env) cells where the key is absent."""
        return sum(
            1
            for row in self.rows
            for env in self.environments
            if row.values.get(env) is None
        )

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "environments": self.environments,
            "rows": [r.to_dict() for r in self.rows],
            "total_keys": self.total_keys,
            "total_missing": self.total_missing,
        }


def pivot_env(
    project: str,
    environments: List[str],
    read_env: Callable[[str, str], Dict[str, str]],
    list_environments: Optional[Callable[[str], List[str]]] = None,
) -> PivotResult:
    """Build a pivot table of all keys across the given environments.

    Args:
        project: The project name.
        environments: List of environment names to include.  If empty and
            *list_environments* is provided the full list is fetched.
        read_env: Callable(project, env) -> {key: value}.
        list_environments: Optional callable(project) -> [env_name, ...].

    Returns:
        A :class:`PivotResult` with one row per unique key.
    """
    if not environments:
        if list_environments is None:
            raise PivotError("No environments specified and list_environments not provided.")
        environments = list_environments(project)
        if not environments:
            raise PivotError(f"Project '{project}' has no environments.")

    env_data: Dict[str, Dict[str, str]] = {}
    for env in environments:
        env_data[env] = read_env(project, env)

    all_keys: List[str] = sorted(
        {key for data in env_data.values() for key in data}
    )

    rows = [
        PivotRow(
            key=key,
            values={env: env_data[env].get(key) for env in environments},
        )
        for key in all_keys
    ]

    return PivotResult(project=project, environments=list(environments), rows=rows)
