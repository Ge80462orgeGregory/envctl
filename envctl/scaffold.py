"""Scaffold a new project environment set with default keys."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from envctl.env_store import write_env, list_environments


DEFAULT_ENVIRONMENTS = ["local", "staging", "production"]

DEFAULT_KEYS: dict[str, str] = {
    "APP_ENV": "",
    "APP_DEBUG": "false",
    "APP_SECRET_KEY": "",
    "DATABASE_URL": "",
    "LOG_LEVEL": "info",
}


class ScaffoldError(Exception):
    """Raised when scaffolding cannot be completed."""


@dataclass
class ScaffoldResult:
    project: str
    environments_created: list[str] = field(default_factory=list)
    keys_written: int = 0
    skipped_environments: list[str] = field(default_factory=list)


def scaffold_project(
    project: str,
    environments: list[str] | None = None,
    extra_keys: dict[str, str] | None = None,
    overwrite: bool = False,
    *,
    _list_environments: Callable[[str], list[str]] = list_environments,
    _write_env: Callable[[str, str, dict[str, str]], None] = write_env,
) -> ScaffoldResult:
    """Create a project scaffold with default environments and keys.

    Args:
        project: The project name to scaffold.
        environments: List of environment names. Defaults to local/staging/production.
        extra_keys: Additional keys to include beyond the defaults.
        overwrite: If True, overwrite existing environments. If False, skip them.

    Returns:
        A ScaffoldResult describing what was created.

    Raises:
        ScaffoldError: If project name is empty or environments list is empty.
    """
    if not project or not project.strip():
        raise ScaffoldError("Project name must not be empty.")

    envs = environments if environments is not None else DEFAULT_ENVIRONMENTS
    if not envs:
        raise ScaffoldError("At least one environment must be specified.")

    keys = {**DEFAULT_KEYS, **(extra_keys or {})}
    existing = set(_list_environments(project))

    result = ScaffoldResult(project=project)

    for env in envs:
        if env in existing and not overwrite:
            result.skipped_environments.append(env)
            continue
        _write_env(project, env, keys)
        result.environments_created.append(env)
        result.keys_written += len(keys)

    return result
