"""blank.py — find or fill keys with empty/blank values in an environment."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


class BlankError(Exception):
    """Raised when a blank operation cannot be completed."""


@dataclass
class BlankResult:
    project: str
    environment: str
    blank_keys: List[str] = field(default_factory=list)
    filled_keys: List[str] = field(default_factory=list)

    def total_blank(self) -> int:
        return len(self.blank_keys)

    def total_filled(self) -> int:
        return len(self.filled_keys)

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "environment": self.environment,
            "blank_keys": self.blank_keys,
            "filled_keys": self.filled_keys,
            "total_blank": self.total_blank(),
            "total_filled": self.total_filled(),
        }


def find_blank(
    project: str,
    environment: str,
    read_env: Callable[[str, str], Dict[str, str]],
) -> BlankResult:
    """Return a BlankResult listing all keys whose value is empty or whitespace-only."""
    data = read_env(project, environment)
    if data is None:
        raise BlankError(f"Environment '{project}/{environment}' not found.")
    blank_keys = sorted(k for k, v in data.items() if not v.strip())
    return BlankResult(
        project=project,
        environment=environment,
        blank_keys=blank_keys,
    )


def fill_blank(
    project: str,
    environment: str,
    filler: str,
    read_env: Callable[[str, str], Dict[str, str]],
    write_env: Callable[[str, str, Dict[str, str]], None],
    keys: Optional[List[str]] = None,
) -> BlankResult:
    """Replace blank values with *filler*.  If *keys* is given, only those keys are considered."""
    data = read_env(project, environment)
    if data is None:
        raise BlankError(f"Environment '{project}/{environment}' not found.")

    result = BlankResult(project=project, environment=environment)
    updated = dict(data)

    candidates = keys if keys is not None else list(data.keys())
    for k in candidates:
        if k not in updated:
            continue
        if not updated[k].strip():
            result.blank_keys.append(k)
            updated[k] = filler
            result.filled_keys.append(k)

    if result.filled_keys:
        write_env(project, environment, updated)

    result.blank_keys.sort()
    result.filled_keys.sort()
    return result
