"""Compute statistics and summary metrics for a project's environments."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List


@dataclass
class EnvStats:
    project: str
    environment: str
    total_keys: int
    empty_values: int
    unique_keys: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "environment": self.environment,
            "total_keys": self.total_keys,
            "empty_values": self.empty_values,
            "unique_keys": self.unique_keys,
        }


@dataclass
class ProjectStats:
    project: str
    environments: List[EnvStats] = field(default_factory=list)

    @property
    def total_keys_across_envs(self) -> int:
        return sum(e.total_keys for e in self.environments)

    @property
    def common_keys(self) -> List[str]:
        if not self.environments:
            return []
        sets = [set(e.unique_keys) for e in self.environments]
        result = sets[0]
        for s in sets[1:]:
            result = result & s
        return sorted(result)

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "total_keys_across_envs": self.total_keys_across_envs,
            "common_keys": self.common_keys,
            "environments": [e.to_dict() for e in self.environments],
        }


class StatsError(Exception):
    pass


def compute_stats(
    project: str,
    list_environments: Callable[[str], List[str]],
    read_env: Callable[[str, str], Dict[str, str]],
) -> ProjectStats:
    envs = list_environments(project)
    if not envs:
        raise StatsError(f"No environments found for project '{project}'.")

    env_stats: List[EnvStats] = []
    for env in envs:
        variables = read_env(project, env)
        total = len(variables)
        empty = sum(1 for v in variables.values() if v == "")
        env_stats.append(
            EnvStats(
                project=project,
                environment=env,
                total_keys=total,
                empty_values=empty,
                unique_keys=sorted(variables.keys()),
            )
        )

    return ProjectStats(project=project, environments=env_stats)
