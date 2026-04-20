"""unique.py — Find keys that exist in one environment but not others."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List


class UniqueError(Exception):
    pass


@dataclass
class UniqueResult:
    project: str
    source_env: str
    compared_envs: List[str]
    unique_keys: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "source_env": self.source_env,
            "compared_envs": self.compared_envs,
            "unique_keys": self.unique_keys,
            "total_unique": self.total_unique,
        }

    @property
    def total_unique(self) -> int:
        return len(self.unique_keys)


def find_unique(
    project: str,
    source_env: str,
    compared_envs: List[str],
    read_fn,
    list_envs_fn=None,
) -> UniqueResult:
    """Return keys present in source_env but absent in ALL compared_envs."""
    if not project:
        raise UniqueError("project must not be empty")
    if not source_env:
        raise UniqueError("source_env must not be empty")

    targets = compared_envs
    if not targets:
        if list_envs_fn is None:
            raise UniqueError("compared_envs is empty and no list_envs_fn provided")
        targets = [e for e in list_envs_fn(project) if e != source_env]

    if not targets:
        raise UniqueError(
            f"No environments to compare against in project '{project}'"
        )

    source = read_fn(project, source_env)
    if not source:
        raise UniqueError(
            f"Environment '{source_env}' in project '{project}' is empty or missing"
        )

    all_other_keys: set = set()
    for env in targets:
        other = read_fn(project, env)
        all_other_keys.update(other.keys())

    unique_keys = {
        k: v for k, v in source.items() if k not in all_other_keys
    }

    return UniqueResult(
        project=project,
        source_env=source_env,
        compared_envs=targets,
        unique_keys=unique_keys,
    )
