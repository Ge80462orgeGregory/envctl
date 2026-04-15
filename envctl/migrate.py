"""Migrate environment variables from one project/environment to another with key remapping."""

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


@dataclass
class MigrateError(Exception):
    message: str

    def __str__(self) -> str:
        return self.message


@dataclass
class MigrateResult:
    source_project: str
    source_env: str
    target_project: str
    target_env: str
    migrated: Dict[str, str] = field(default_factory=dict)
    skipped: List[str] = field(default_factory=list)
    remapped: Dict[str, str] = field(default_factory=dict)

    @property
    def total_migrated(self) -> int:
        return len(self.migrated)

    @property
    def total_skipped(self) -> int:
        return len(self.skipped)

    def to_dict(self) -> dict:
        return {
            "source_project": self.source_project,
            "source_env": self.source_env,
            "target_project": self.target_project,
            "target_env": self.target_env,
            "migrated": self.migrated,
            "skipped": self.skipped,
            "remapped": self.remapped,
            "total_migrated": self.total_migrated,
            "total_skipped": self.total_skipped,
        }


def migrate_env(
    source_project: str,
    source_env: str,
    target_project: str,
    target_env: str,
    read_env: Callable[[str, str], Dict[str, str]],
    write_env: Callable[[str, str, Dict[str, str]], None],
    key_map: Optional[Dict[str, str]] = None,
    keys: Optional[List[str]] = None,
    overwrite: bool = False,
) -> MigrateResult:
    """Migrate variables from source to target, optionally remapping keys."""
    source_vars = read_env(source_project, source_env)
    if not source_vars:
        raise MigrateError(f"Source '{source_project}/{source_env}' is empty or does not exist.")

    target_vars = read_env(target_project, target_env)
    key_map = key_map or {}
    selected = {k: v for k, v in source_vars.items() if keys is None or k in keys}

    result = MigrateResult(
        source_project=source_project,
        source_env=source_env,
        target_project=target_project,
        target_env=target_env,
    )

    updated = dict(target_vars)
    for src_key, value in selected.items():
        dest_key = key_map.get(src_key, src_key)
        if dest_key in target_vars and not overwrite:
            result.skipped.append(src_key)
            continue
        updated[dest_key] = value
        result.migrated[dest_key] = value
        if dest_key != src_key:
            result.remapped[src_key] = dest_key

    write_env(target_project, target_env, updated)
    return result
