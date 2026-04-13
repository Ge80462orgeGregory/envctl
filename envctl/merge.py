"""Merge two environments into a target environment."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


class MergeError(Exception):
    """Raised when a merge operation cannot be completed."""


@dataclass
class MergeResult:
    project: str
    source_a: str
    source_b: str
    target: str
    added: List[str] = field(default_factory=list)
    overwritten: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    @property
    def total_changes(self) -> int:
        return len(self.added) + len(self.overwritten)


def merge_envs(
    project: str,
    source_a: str,
    source_b: str,
    target: str,
    *,
    overwrite: bool = False,
    keys: Optional[List[str]] = None,
    read_env: Callable[[str, str], Dict[str, str]] = None,
    write_env: Callable[[str, str, Dict[str, str]], None] = None,
) -> MergeResult:
    """Merge source_a and source_b into target for the given project.

    Keys from source_b take precedence over source_a when both define the same key.
    Existing keys in target are only overwritten when *overwrite* is True.
    """
    if read_env is None or write_env is None:
        from envctl.env_store import read_env as _read, write_env as _write
        read_env = read_env or _read
        write_env = write_env or _write

    env_a = read_env(project, source_a)
    env_b = read_env(project, source_b)
    current = read_env(project, target)

    # Merge a then b so b wins on conflicts between the two sources
    merged_source: Dict[str, str] = {**env_a, **env_b}

    if keys is not None:
        unknown = set(keys) - set(merged_source)
        if unknown:
            raise MergeError(
                f"Keys not found in either source: {', '.join(sorted(unknown))}"
            )
        merged_source = {k: v for k, v in merged_source.items() if k in keys}

    result = MergeResult(
        project=project,
        source_a=source_a,
        source_b=source_b,
        target=target,
    )

    updated = dict(current)
    for key, value in merged_source.items():
        if key not in current:
            updated[key] = value
            result.added.append(key)
        elif current[key] == value:
            result.skipped.append(key)
        elif overwrite:
            updated[key] = value
            result.overwritten.append(key)
        else:
            result.skipped.append(key)

    write_env(project, target, updated)
    return result
