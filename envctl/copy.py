"""Logic for copying environment variables from one environment to another."""

from typing import Optional
from envctl.env_store import read_env, write_env


class CopyError(Exception):
    """Raised when a copy operation cannot be completed."""


def copy_env(
    src_project: str,
    src_env: str,
    dst_project: str,
    dst_env: str,
    keys: Optional[list[str]] = None,
    overwrite: bool = False,
) -> dict[str, str]:
    """Copy environment variables from src to dst.

    Args:
        src_project: Source project name.
        src_env: Source environment name (e.g. 'staging').
        dst_project: Destination project name.
        dst_env: Destination environment name (e.g. 'production').
        keys: Optional list of specific keys to copy. Copies all if None.
        overwrite: If True, overwrite existing keys in destination.

    Returns:
        A dict of the keys that were actually copied.

    Raises:
        CopyError: If the source environment is empty or keys are not found.
    """
    src_vars = read_env(src_project, src_env)
    if not src_vars:
        raise CopyError(
            f"Source environment '{src_env}' for project '{src_project}' is empty or does not exist."
        )

    if keys is not None:
        missing = [k for k in keys if k not in src_vars]
        if missing:
            raise CopyError(
                f"Keys not found in source environment: {', '.join(missing)}"
            )
        src_vars = {k: src_vars[k] for k in keys}

    dst_vars = read_env(dst_project, dst_env)

    copied: dict[str, str] = {}
    for key, value in src_vars.items():
        if key in dst_vars and not overwrite:
            continue
        dst_vars[key] = value
        copied[key] = value

    if copied:
        write_env(dst_project, dst_env, dst_vars)

    return copied
