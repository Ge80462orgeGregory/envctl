"""Snapshot: capture and restore point-in-time copies of a project's environments."""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from typing import Dict, List

from envctl.env_store import list_environments, read_env, write_env


class SnapshotError(Exception):
    """Raised when a snapshot operation fails."""


@dataclass
class Snapshot:
    project: str
    label: str
    created_at: str
    envs: Dict[str, Dict[str, str]] = field(default_factory=dict)


@dataclass
class RestoreResult:
    project: str
    label: str
    restored_envs: List[str] = field(default_factory=list)
    total_keys: int = 0


def take_snapshot(
    project: str,
    label: str,
    *,
    list_environments_fn=list_environments,
    read_env_fn=read_env,
) -> Snapshot:
    """Capture all environments for *project* into a Snapshot."""
    if not project:
        raise SnapshotError("project name must not be empty")
    if not label:
        raise SnapshotError("snapshot label must not be empty")

    envs_found = list_environments_fn(project)
    snapshot_envs: Dict[str, Dict[str, str]] = {}
    for env in envs_found:
        snapshot_envs[env] = dict(read_env_fn(project, env))

    created_at = datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z"
    return Snapshot(project=project, label=label, created_at=created_at, envs=snapshot_envs)


def restore_snapshot(
    snapshot: Snapshot,
    *,
    write_env_fn=write_env,
) -> RestoreResult:
    """Write every environment captured in *snapshot* back to the store."""
    if not snapshot.envs:
        raise SnapshotError("snapshot contains no environments to restore")

    result = RestoreResult(project=snapshot.project, label=snapshot.label)
    for env_name, variables in snapshot.envs.items():
        write_env_fn(snapshot.project, env_name, variables)
        result.restored_envs.append(env_name)
        result.total_keys += len(variables)
    return result
