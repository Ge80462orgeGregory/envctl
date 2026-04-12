"""Logic for renaming an environment within a project."""

from typing import Optional
from envctl.env_store import read_env, write_env, _env_file_path
import os


class RenameError(Exception):
    """Raised when a rename operation cannot be completed."""
    pass


def rename_env(
    project: str,
    src_env: str,
    dst_env: str,
    envs_dir: str,
    overwrite: bool = False,
    read_fn=None,
    write_fn=None,
    exists_fn=None,
    remove_fn=None,
) -> dict:
    """Rename src_env to dst_env for the given project.

    Returns a dict summarising the operation:
        {"project": ..., "src": ..., "dst": ..., "keys_moved": int}

    Raises RenameError if:
    - src_env does not exist (is empty / missing)
    - dst_env already exists and overwrite is False
    """
    _read = read_fn or (lambda p, e: read_env(p, e, envs_dir=envs_dir))
    _write = write_fn or (lambda p, e, v: write_env(p, e, v, envs_dir=envs_dir))
    _exists = exists_fn or (lambda p, e: os.path.exists(_env_file_path(p, e, envs_dir=envs_dir)))
    _remove = remove_fn or (lambda p, e: os.remove(_env_file_path(p, e, envs_dir=envs_dir)))

    src_vars = _read(project, src_env)
    if not src_vars:
        raise RenameError(
            f"Source environment '{src_env}' for project '{project}' does not exist or is empty."
        )

    if _exists(project, dst_env) and not overwrite:
        raise RenameError(
            f"Destination environment '{dst_env}' already exists. "
            "Use --overwrite to replace it."
        )

    _write(project, dst_env, src_vars)
    _remove(project, src_env)

    return {
        "project": project,
        "src": src_env,
        "dst": dst_env,
        "keys_moved": len(src_vars),
    }
