"""Track and retrieve the change history of an environment's variables."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, List, Optional


@dataclass
class HistoryEntry:
    timestamp: str
    action: str
    project: str
    environment: str
    changes: Dict[str, object]
    actor: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "action": self.action,
            "project": self.project,
            "environment": self.environment,
            "changes": self.changes,
            "actor": self.actor,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "HistoryEntry":
        return cls(
            timestamp=data["timestamp"],
            action=data["action"],
            project=data["project"],
            environment=data["environment"],
            changes=data.get("changes", {}),
            actor=data.get("actor"),
        )


class HistoryError(Exception):
    pass


def _history_file_path(envs_dir: str, project: str, environment: str) -> Path:
    return Path(envs_dir) / project / f"{environment}.history.jsonl"


def record_history(
    envs_dir: str,
    project: str,
    environment: str,
    action: str,
    changes: Dict[str, object],
    actor: Optional[str] = None,
    _now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
) -> HistoryEntry:
    """Append a history entry for the given project/environment."""
    entry = HistoryEntry(
        timestamp=_now().isoformat(),
        action=action,
        project=project,
        environment=environment,
        changes=changes,
        actor=actor,
    )
    path = _history_file_path(envs_dir, project, environment)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry.to_dict()) + "\n")
    return entry


def read_history(
    envs_dir: str,
    project: str,
    environment: str,
    limit: Optional[int] = None,
) -> List[HistoryEntry]:
    """Return history entries, newest first, optionally limited."""
    path = _history_file_path(envs_dir, project, environment)
    if not path.exists():
        return []
    entries: List[HistoryEntry] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                entries.append(HistoryEntry.from_dict(json.loads(line)))
    entries.reverse()
    if limit is not None:
        entries = entries[:limit]
    return entries
