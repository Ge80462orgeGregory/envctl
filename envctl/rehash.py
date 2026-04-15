"""rehash: Recompute and update stored checksums for an environment."""

from dataclasses import dataclass, field
from typing import Callable, Dict, List

from envctl.checksum import compute_checksum


class RehashError(Exception):
    pass


@dataclass
class RehashResult:
    project: str
    environment: str
    updated: List[str] = field(default_factory=list)
    unchanged: List[str] = field(default_factory=list)

    @property
    def total_updated(self) -> int:
        return len(self.updated)

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "environment": self.environment,
            "updated": self.updated,
            "unchanged": self.unchanged,
            "total_updated": self.total_updated,
        }


def rehash_env(
    project: str,
    environment: str,
    read_env: Callable[[str, str], Dict[str, str]],
    read_checksums: Callable[[str, str], Dict[str, str]],
    write_checksums: Callable[[str, str, Dict[str, str]], None],
) -> RehashResult:
    """Recompute per-key checksums and persist any that have changed."""
    variables = read_env(project, environment)
    if not variables:
        raise RehashError(
            f"No variables found for '{project}/{environment}'. "
            "Cannot rehash an empty environment."
        )

    existing: Dict[str, str] = read_checksums(project, environment)
    updated_checksums: Dict[str, str] = dict(existing)

    result = RehashResult(project=project, environment=environment)

    for key, value in sorted(variables.items()):
        new_hash = compute_checksum({key: value}).checksum
        old_hash = existing.get(key)
        if old_hash != new_hash:
            updated_checksums[key] = new_hash
            result.updated.append(key)
        else:
            result.unchanged.append(key)

    # Remove checksums for keys that no longer exist
    stale = [k for k in existing if k not in variables]
    for k in stale:
        del updated_checksums[k]
        if k not in result.updated:
            result.updated.append(k)

    write_checksums(project, environment, updated_checksums)
    return result
