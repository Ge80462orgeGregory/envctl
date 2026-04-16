"""intersect.py — find keys common to two environments."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List


class IntersectError(Exception):
    pass


@dataclass
class IntersectResult:
    project: str
    source_env: str
    target_env: str
    common_keys: List[str] = field(default_factory=list)
    common_with_same_value: List[str] = field(default_factory=list)
    common_with_diff_value: List[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.common_keys)

    def to_dict(self) -> Dict:
        return {
            "project": self.project,
            "source_env": self.source_env,
            "target_env": self.target_env,
            "common_keys": self.common_keys,
            "common_with_same_value": self.common_with_same_value,
            "common_with_diff_value": self.common_with_diff_value,
            "total": self.total,
        }


def intersect_envs(
    project: str,
    source_env: str,
    target_env: str,
    read_env,
) -> IntersectResult:
    src = read_env(project, source_env)
    tgt = read_env(project, target_env)

    if not src:
        raise IntersectError(f"Environment '{source_env}' not found in project '{project}'")
    if not tgt:
        raise IntersectError(f"Environment '{target_env}' not found in project '{project}'")

    common = sorted(set(src) & set(tgt))
    same = [k for k in common if src[k] == tgt[k]]
    diff = [k for k in common if src[k] != tgt[k]]

    return IntersectResult(
        project=project,
        source_env=source_env,
        target_env=target_env,
        common_keys=common,
        common_with_same_value=same,
        common_with_diff_value=diff,
    )
