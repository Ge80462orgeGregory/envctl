"""Squash multiple environments into one by merging their keys."""
from dataclasses import dataclass, field
from typing import Callable, Dict, List


class SquashError(Exception):
    pass


@dataclass
class SquashResult:
    project: str
    sources: List[str]
    target: str
    merged: Dict[str, str] = field(default_factory=dict)
    conflicts: Dict[str, List[str]] = field(default_factory=dict)

    @property
    def total_keys(self) -> int:
        return len(self.merged)

    @property
    def total_conflicts(self) -> int:
        return len(self.conflicts)

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "sources": self.sources,
            "target": self.target,
            "total_keys": self.total_keys,
            "total_conflicts": self.total_conflicts,
            "conflicts": self.conflicts,
        }


def squash_envs(
    project: str,
    sources: List[str],
    target: str,
    read_env: Callable,
    write_env: Callable,
    overwrite: bool = False,
) -> SquashResult:
    if not sources:
        raise SquashError("At least one source environment is required.")
    if target in sources:
        raise SquashError("Target environment cannot be one of the sources.")

    merged: Dict[str, str] = {}
    conflicts: Dict[str, List[str]] = {}

    for env in sources:
        data = read_env(project, env)
        for key, value in data.items():
            if key in merged:
                if merged[key] != value:
                    conflicts.setdefault(key, [merged[key]])
                    if value not in conflicts[key]:
                        conflicts[key].append(value)
                    if overwrite:
                        merged[key] = value
            else:
                merged[key] = value

    write_env(project, target, merged)
    return SquashResult(
        project=project,
        sources=sources,
        target=target,
        merged=merged,
        conflicts=conflicts,
    )
