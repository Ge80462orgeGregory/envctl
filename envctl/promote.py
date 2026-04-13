"""Promote an environment's variables to another environment (e.g. staging -> production)."""

from dataclasses import dataclass, field
from typing import Optional

from envctl.env_store import read_env, write_env


class PromoteError(Exception):
    """Raised when a promotion operation fails."""


@dataclass
class PromoteResult:
    promoted: dict = field(default_factory=dict)
    skipped: dict = field(default_factory=dict)
    overwritten: dict = field(default_factory=dict)


def promote_env(
    project: str,
    source_env: str,
    target_env: str,
    keys: Optional[list] = None,
    overwrite: bool = False,
    read_fn=read_env,
    write_fn=write_env,
) -> PromoteResult:
    """Promote variables from source_env to target_env within a project.

    Args:
        project: The project name.
        source_env: The environment to promote from.
        target_env: The environment to promote to.
        keys: Optional list of specific keys to promote. Promotes all if None.
        overwrite: If True, overwrite conflicting keys in target.
        read_fn: Injectable read function for testing.
        write_fn: Injectable write function for testing.

    Returns:
        A PromoteResult describing what was promoted, skipped, or overwritten.

    Raises:
        PromoteError: If source and target are the same or source is empty.
    """
    if source_env == target_env:
        raise PromoteError(f"Source and target environments must differ (got '{source_env}').")

    source_vars = read_fn(project, source_env)
    if not source_vars:
        raise PromoteError(f"Source environment '{source_env}' in project '{project}' is empty or does not exist.")

    target_vars = read_fn(project, target_env)

    candidates = {k: v for k, v in source_vars.items() if keys is None or k in keys}

    if keys:
        missing = set(keys) - set(source_vars)
        if missing:
            raise PromoteError(f"Keys not found in source environment: {', '.join(sorted(missing))}")

    result = PromoteResult()
    updated_target = dict(target_vars)

    for key, value in candidates.items():
        if key in target_vars:
            if target_vars[key] == value:
                result.skipped[key] = value
            elif overwrite:
                result.overwritten[key] = value
                updated_target[key] = value
            else:
                result.skipped[key] = value
        else:
            result.promoted[key] = value
            updated_target[key] = value

    write_fn(project, target_env, updated_target)
    return result
