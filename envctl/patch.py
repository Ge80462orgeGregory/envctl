"""Apply a partial update (patch) to an environment, setting or unsetting specific keys."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envctl.env_store import read_env, write_env


class PatchError(Exception):
    """Raised when a patch operation fails."""


@dataclass
class PatchResult:
    project: str
    environment: str
    set_keys: List[str] = field(default_factory=list)
    unset_keys: List[str] = field(default_factory=list)
    skipped_keys: List[str] = field(default_factory=list)

    @property
    def total_changes(self) -> int:
        return len(self.set_keys) + len(self.unset_keys)


def patch_env(
    project: str,
    environment: str,
    set_vars: Optional[Dict[str, str]] = None,
    unset_keys: Optional[List[str]] = None,
    overwrite: bool = True,
    *,
    _read=read_env,
    _write=write_env,
) -> PatchResult:
    """Apply a partial update to an environment.

    Args:
        project: Project name.
        environment: Environment name.
        set_vars: Keys and values to set.
        unset_keys: Keys to remove.
        overwrite: If False, existing keys are skipped rather than overwritten.

    Returns:
        PatchResult summarising the changes made.

    Raises:
        PatchError: If both set_vars and unset_keys are empty.
    """
    set_vars = set_vars or {}
    unset_keys = unset_keys or []

    if not set_vars and not unset_keys:
        raise PatchError("patch_env requires at least one set or unset operation")

    current = _read(project, environment)
    result = PatchResult(project=project, environment=environment)

    updated = dict(current)

    for key, value in set_vars.items():
        if not overwrite and key in updated:
            result.skipped_keys.append(key)
            continue
        updated[key] = value
        result.set_keys.append(key)

    for key in unset_keys:
        if key in updated:
            del updated[key]
            result.unset_keys.append(key)
        else:
            result.skipped_keys.append(key)

    _write(project, environment, updated)
    return result
