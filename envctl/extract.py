"""Extract a subset of keys from an environment into a new environment."""

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


class ExtractError(Exception):
    pass


@dataclass
class ExtractResult:
    project: str
    source_env: str
    target_env: str
    extracted: Dict[str, str] = field(default_factory=dict)
    skipped: List[str] = field(default_factory=list)

    @property
    def total_extracted(self) -> int:
        return len(self.extracted)

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "source_env": self.source_env,
            "target_env": self.target_env,
            "extracted": self.extracted,
            "skipped": self.skipped,
            "total_extracted": self.total_extracted,
        }


def extract_env(
    project: str,
    source_env: str,
    target_env: str,
    keys: List[str],
    read: Callable[[str, str], Dict[str, str]],
    write: Callable[[str, str, Dict[str, str]], None],
    overwrite: bool = False,
) -> ExtractResult:
    """Extract specific keys from source_env into target_env."""
    if not keys:
        raise ExtractError("No keys specified for extraction.")

    source_vars = read(project, source_env)
    if not source_vars:
        raise ExtractError(f"Source environment '{source_env}' is empty or does not exist.")

    target_vars = read(project, target_env)

    result = ExtractResult(
        project=project,
        source_env=source_env,
        target_env=target_env,
    )

    updated = dict(target_vars)

    for key in keys:
        if key not in source_vars:
            result.skipped.append(key)
            continue
        if key in target_vars and not overwrite:
            result.skipped.append(key)
            continue
        updated[key] = source_vars[key]
        result.extracted[key] = source_vars[key]

    if result.extracted:
        write(project, target_env, updated)

    return result
