"""Rotate (regenerate) keys in an environment by applying a transform function."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from envctl.env_store import read_env, write_env


class RotateError(Exception):
    """Raised when rotation cannot be completed."""


@dataclass
class RotateResult:
    project: str
    environment: str
    rotated: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    @property
    def total_rotated(self) -> int:
        return len(self.rotated)


def rotate_env(
    project: str,
    environment: str,
    keys: Optional[List[str]],
    transform: Callable[[str, str], str],
    *,
    dry_run: bool = False,
    _read: Callable = read_env,
    _write: Callable = write_env,
) -> RotateResult:
    """Apply *transform(key, value) -> new_value* to selected keys.

    Args:
        project: Project name.
        environment: Environment name (e.g. ``staging``).
        keys: Explicit list of keys to rotate.  ``None`` means all keys.
        transform: Callable that receives the key name and current value and
            returns the replacement value.
        dry_run: When *True* the updated env is **not** persisted.

    Returns:
        A :class:`RotateResult` describing what changed.

    Raises:
        RotateError: If *keys* contains a key not present in the environment.
    """
    current: Dict[str, str] = _read(project, environment)

    if not current:
        raise RotateError(
            f"Environment '{environment}' for project '{project}' is empty or does not exist."
        )

    if keys:
        missing = [k for k in keys if k not in current]
        if missing:
            raise RotateError(
                f"Keys not found in '{project}/{environment}': {', '.join(missing)}"
            )
        targets = keys
    else:
        targets = list(current.keys())

    result = RotateResult(project=project, environment=environment)
    updated = dict(current)

    for key in targets:
        old_val = current[key]
        new_val = transform(key, old_val)
        if new_val != old_val:
            updated[key] = new_val
            result.rotated.append(key)
        else:
            result.skipped.append(key)

    if result.rotated and not dry_run:
        _write(project, environment, updated)

    return result
