"""Logic for deleting an environment or specific keys from an environment."""

from typing import Optional

from envctl.env_store import read_env, write_env, delete_env, list_environments


class DeleteError(Exception):
    """Raised when a delete operation fails."""


def delete_env_or_keys(
    project: str,
    environment: str,
    keys: Optional[list[str]] = None,
    *,
    store_read=read_env,
    store_write=write_env,
    store_delete=delete_env,
    store_list=list_environments,
) -> dict:
    """Delete an entire environment or specific keys from it.

    Args:
        project: Project name.
        environment: Environment name (e.g. 'staging').
        keys: If provided, only these keys are removed. If None, the whole
              environment file is deleted.
        store_read / store_write / store_delete / store_list: Injectable
              storage helpers (used for testing).

    Returns:
        A dict with ``removed_keys`` (list) and ``deleted_env`` (bool).

    Raises:
        DeleteError: If the environment does not exist.
    """
    existing_envs = store_list(project)
    if environment not in existing_envs:
        raise DeleteError(
            f"Environment '{environment}' not found in project '{project}'."
        )

    if keys is None:
        store_delete(project, environment)
        return {"removed_keys": [], "deleted_env": True}

    current = store_read(project, environment)
    missing = [k for k in keys if k not in current]
    if missing:
        raise DeleteError(
            f"Keys not found in '{project}/{environment}': {', '.join(missing)}"
        )

    for key in keys:
        del current[key]

    store_write(project, environment, current)
    return {"removed_keys": list(keys), "deleted_env": False}
