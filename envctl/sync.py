"""Sync environment variables between environments."""

from typing import Optional
from envctl.env_store import read_env, write_env, list_environments


class SyncConflict(Exception):
    """Raised when a sync conflict is detected and no resolution strategy is given."""
    pass


def sync_envs(
    project: str,
    source_env: str,
    target_env: str,
    overwrite: bool = False,
    keys: Optional[list[str]] = None,
) -> dict:
    """
    Sync variables from source_env to target_env for a given project.

    Args:
        project: The project name.
        source_env: The environment to copy from.
        target_env: The environment to copy to.
        overwrite: If True, overwrite existing keys in target. If False, raise SyncConflict.
        keys: Optional list of specific keys to sync. If None, sync all keys.

    Returns:
        A dict with keys 'added', 'updated', 'skipped' listing affected variable names.
    """
    source = read_env(project, source_env)
    target = read_env(project, target_env)

    keys_to_sync = keys if keys is not None else list(source.keys())

    added = []
    updated = []
    skipped = []
    conflicts = []

    for key in keys_to_sync:
        if key not in source:
            skipped.append(key)
            continue

        if key in target and target[key] != source[key]:
            if not overwrite:
                conflicts.append(key)
            else:
                updated.append(key)
        elif key not in target:
            added.append(key)
        else:
            skipped.append(key)

    if conflicts:
        raise SyncConflict(
            f"Conflicts detected for keys: {', '.join(conflicts)}. "
            "Use --overwrite to force sync."
        )

    merged = dict(target)
    for key in added + updated:
        merged[key] = source[key]

    write_env(project, target_env, merged)

    return {"added": added, "updated": updated, "skipped": skipped}
