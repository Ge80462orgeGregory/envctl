"""Generate a sample/skeleton env file with placeholder values for a project environment."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


class SampleError(Exception):
    pass


@dataclass
class SampleResult:
    project: str
    environment: str
    keys: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    def total_generated(self) -> int:
        return len(self.keys)

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "environment": self.environment,
            "keys": self.keys,
            "skipped": self.skipped,
            "total_generated": self.total_generated(),
        }


def sample_env(
    project: str,
    environment: str,
    keys: List[str],
    placeholder: str = "CHANGEME",
    overwrite: bool = False,
    *,
    read_env,
    write_env,
) -> SampleResult:
    """Write placeholder values for the given keys into the target env.

    Args:
        project: Project name.
        environment: Environment name.
        keys: List of key names to scaffold.
        placeholder: Value to assign to each new key.
        overwrite: If True, overwrite keys that already have a value.
        read_env: Callable(project, environment) -> dict.
        write_env: Callable(project, environment, dict) -> None.

    Returns:
        SampleResult describing what was written and what was skipped.
    """
    if not keys:
        raise SampleError("No keys provided to sample.")

    existing = read_env(project, environment)
    updated = dict(existing)
    written: List[str] = []
    skipped: List[str] = []

    for key in keys:
        key = key.strip()
        if not key:
            continue
        if key in existing and not overwrite:
            skipped.append(key)
        else:
            updated[key] = placeholder
            written.append(key)

    if written:
        write_env(project, environment, updated)

    return SampleResult(
        project=project,
        environment=environment,
        keys=written,
        skipped=skipped,
    )
