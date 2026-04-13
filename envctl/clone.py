"""Clone an entire project's environments to a new project name."""

from dataclasses import dataclass, field
from typing import Callable, Optional

from envctl.env_store import list_environments, read_env, write_env


class CloneError(Exception):
    """Raised when a clone operation cannot be completed."""


@dataclass
class CloneResult:
    source_project: str
    dest_project: str
    cloned_envs: list[str] = field(default_factory=list)
    skipped_envs: list[str] = field(default_factory=list)

    @property
    def total_cloned(self) -> int:
        return len(self.cloned_envs)


def clone_project(
    source_project: str,
    dest_project: str,
    *,
    overwrite: bool = False,
    envs_dir: Optional[str] = None,
    _list_environments: Callable = list_environments,
    _read_env: Callable = read_env,
    _write_env: Callable = write_env,
) -> CloneResult:
    """Clone all environments from source_project into dest_project.

    Args:
        source_project: The project to clone from.
        dest_project: The project to clone into.
        overwrite: If True, overwrite existing environments in dest_project.
        envs_dir: Optional override for the environments directory.

    Raises:
        CloneError: If source_project has no environments or source == dest.
    """
    if source_project == dest_project:
        raise CloneError("Source and destination project names must differ.")

    kwargs = {"envs_dir": envs_dir} if envs_dir else {}

    source_envs = _list_environments(source_project, **kwargs)
    if not source_envs:
        raise CloneError(f"No environments found for project '{source_project}'.")

    dest_envs = set(_list_environments(dest_project, **kwargs))

    result = CloneResult(source_project=source_project, dest_project=dest_project)

    for env_name in source_envs:
        if env_name in dest_envs and not overwrite:
            result.skipped_envs.append(env_name)
            continue

        variables = _read_env(source_project, env_name, **kwargs)
        _write_env(dest_project, env_name, variables, **kwargs)
        result.cloned_envs.append(env_name)

    return result
