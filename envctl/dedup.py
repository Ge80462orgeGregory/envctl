"""Deduplication of environment variable keys across environments."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List


class DedupError(Exception):
    pass


@dataclass
class DedupResult:
    project: str
    duplicates: Dict[str, List[str]]  # key -> list of envs that share it
    total_duplicate_keys: int = 0

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "duplicates": self.duplicates,
            "total_duplicate_keys": self.total_duplicate_keys,
        }


def find_duplicates(
    project: str,
    list_environments: Callable[[str], List[str]],
    read_env: Callable[[str, str], Dict[str, str]],
) -> DedupResult:
    """Find keys that appear in more than one environment for a project."""
    envs = list_environments(project)
    if not envs:
        raise DedupError(f"No environments found for project '{project}'.")

    key_to_envs: Dict[str, List[str]] = {}

    for env in envs:
        variables = read_env(project, env)
        for key in variables:
            key_to_envs.setdefault(key, []).append(env)

    duplicates = {k: v for k, v in key_to_envs.items() if len(v) > 1}

    return DedupResult(
        project=project,
        duplicates=duplicates,
        total_duplicate_keys=len(duplicates),
    )
