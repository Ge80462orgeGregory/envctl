"""Split an environment into two environments based on key prefixes or a key list."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


class SplitError(Exception):
    pass


@dataclass
class SplitResult:
    project: str
    source_env: str
    target_a: str
    target_b: str
    keys_to_a: Dict[str, str] = field(default_factory=dict)
    keys_to_b: Dict[str, str] = field(default_factory=dict)

    @property
    def total_to_a(self) -> int:
        return len(self.keys_to_a)

    @property
    def total_to_b(self) -> int:
        return len(self.keys_to_b)

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "source_env": self.source_env,
            "target_a": self.target_a,
            "target_b": self.target_b,
            "keys_to_a": self.keys_to_a,
            "keys_to_b": self.keys_to_b,
            "total_to_a": self.total_to_a,
            "total_to_b": self.total_to_b,
        }


def split_env(
    project: str,
    source_env: str,
    target_a: str,
    target_b: str,
    *,
    prefixes_a: Optional[List[str]] = None,
    keys_a: Optional[List[str]] = None,
    read_fn,
    write_fn,
) -> SplitResult:
    """Split source_env into target_a and target_b.

    Keys are routed to target_a if they match ``prefixes_a`` or appear in
    ``keys_a``; all remaining keys go to target_b.  At least one of
    ``prefixes_a`` or ``keys_a`` must be provided.
    """
    if not prefixes_a and not keys_a:
        raise SplitError("At least one of 'prefixes_a' or 'keys_a' must be specified.")

    if target_a == target_b:
        raise SplitError("target_a and target_b must be different environments.")

    source = read_fn(project, source_env)
    if not source:
        raise SplitError(f"Source environment '{source_env}' in project '{project}' is empty or does not exist.")

    prefixes_a = prefixes_a or []
    keys_a = set(keys_a or [])

    bucket_a: Dict[str, str] = {}
    bucket_b: Dict[str, str] = {}

    for key, value in source.items():
        in_a = key in keys_a or any(key.startswith(p) for p in prefixes_a)
        if in_a:
            bucket_a[key] = value
        else:
            bucket_b[key] = value

    write_fn(project, target_a, bucket_a)
    write_fn(project, target_b, bucket_b)

    return SplitResult(
        project=project,
        source_env=source_env,
        target_a=target_a,
        target_b=target_b,
        keys_to_a=bucket_a,
        keys_to_b=bucket_b,
    )
