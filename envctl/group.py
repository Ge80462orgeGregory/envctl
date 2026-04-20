"""Group environment variables by a shared key prefix into named groups."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


class GroupError(Exception):
    pass


@dataclass
class GroupResult:
    project: str
    environment: str
    groups: Dict[str, Dict[str, str]] = field(default_factory=dict)
    ungrouped: Dict[str, str] = field(default_factory=dict)

    def total_groups(self) -> int:
        return len(self.groups)

    def total_keys(self) -> int:
        return sum(len(v) for v in self.groups.values()) + len(self.ungrouped)

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "environment": self.environment,
            "groups": self.groups,
            "ungrouped": self.ungrouped,
            "total_groups": self.total_groups(),
            "total_keys": self.total_keys(),
        }


def group_env(
    project: str,
    environment: str,
    read_env,
    prefixes: Optional[List[str]] = None,
    separator: str = "_",
) -> GroupResult:
    """Group variables by prefix. If prefixes is None, auto-detect from keys."""
    variables = read_env(project, environment)
    if variables is None:
        raise GroupError(
            f"Environment '{environment}' not found in project '{project}'."
        )

    groups: Dict[str, Dict[str, str]] = {}
    ungrouped: Dict[str, str] = {}

    if prefixes is None:
        # Auto-detect: collect all keys that share a common prefix (first segment)
        prefix_counts: Dict[str, int] = {}
        for key in variables:
            if separator in key:
                seg = key.split(separator, 1)[0]
                prefix_counts[seg] = prefix_counts.get(seg, 0) + 1
        prefixes = [p for p, count in prefix_counts.items() if count > 1]

    prefix_set = set(prefixes)

    for key, value in variables.items():
        matched = False
        if separator in key:
            seg = key.split(separator, 1)[0]
            if seg in prefix_set:
                groups.setdefault(seg, {})[key] = value
                matched = True
        if not matched:
            ungrouped[key] = value

    return GroupResult(
        project=project,
        environment=environment,
        groups=groups,
        ungrouped=ungrouped,
    )
