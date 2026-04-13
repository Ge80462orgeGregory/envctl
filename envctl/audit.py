"""Audit log for tracking environment variable changes."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import List, Optional

from envctl.config import get_envs_dir


@dataclass
class AuditEntry:
    timestamp: str
    action: str
    project: str
    environment: str
    keys: List[str]
    detail: Optional[str] = None


class AuditError(Exception):
    pass


def _audit_file_path(envs_dir: str) -> str:
    return os.path.join(envs_dir, ".audit.log")


def record(action: str, project: str, environment: str, keys: List[str], detail: Optional[str] = None, envs_dir: Optional[str] = None) -> AuditEntry:
    """Append an audit entry to the log file."""
    if envs_dir is None:
        envs_dir = get_envs_dir()

    entry = AuditEntry(
        timestamp=datetime.now(timezone.utc).isoformat(),
        action=action,
        project=project,
        environment=environment,
        keys=keys,
        detail=detail,
    )

    audit_path = _audit_file_path(envs_dir)
    with open(audit_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(entry)) + "\n")

    return entry


def read_log(envs_dir: Optional[str] = None, project: Optional[str] = None, environment: Optional[str] = None) -> List[AuditEntry]:
    """Read and optionally filter audit log entries."""
    if envs_dir is None:
        envs_dir = get_envs_dir()

    audit_path = _audit_file_path(envs_dir)
    if not os.path.exists(audit_path):
        return []

    entries: List[AuditEntry] = []
    with open(audit_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                entries.append(AuditEntry(**data))
            except (json.JSONDecodeError, TypeError):
                raise AuditError(f"Malformed audit log entry: {line!r}")

    if project is not None:
        entries = [e for e in entries if e.project == project]
    if environment is not None:
        entries = [e for e in entries if e.environment == environment]

    return entries


def format_log(entries: List[AuditEntry]) -> str:
    """Format audit entries for human-readable display."""
    if not entries:
        return "No audit entries found."
    lines = []
    for e in entries:
        keys_str = ", ".join(e.keys) if e.keys else "(none)"
        detail_str = f" [{e.detail}]" if e.detail else ""
        lines.append(f"{e.timestamp}  {e.action:10s}  {e.project}/{e.environment}  keys: {keys_str}{detail_str}")
    return "\n".join(lines)
