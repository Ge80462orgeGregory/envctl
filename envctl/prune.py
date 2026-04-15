"""Prune stale or unused keys from an environment by comparing against a reference."""

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


class PruneError(Exception):
    """Raised when pruning fails."""


@dataclass
class PruneResult:
    project: str
    environment: str
    reference_environment: str
    removed_keys: List[str] = field(default_factory=list)
    retained_keys: List[str] = field(default_factory=list)

    @property
    def total_removed(self) -> int:
        return len(self.removed_keys)

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "environment": self.environment,
            "reference_environment": self.reference_environment,
            "removed_keys": sorted(self.removed_keys),
            "retained_keys": sorted(self.retained_keys),
            "total_removed": self.total_removed,
        }


def prune_env(
    project: str,
    environment: str,
    reference_environment: str,
    read_env: Callable[[str, str], Dict[str, str]],
    write_env: Callable[[str, str, Dict[str, str]], None],
    dry_run: bool = False,
) -> PruneResult:
    """Remove keys from *environment* that do not exist in *reference_environment*.

    Args:
        project: Project name.
        environment: The environment to prune.
        reference_environment: The environment whose keys act as the allowed set.
        read_env: Callable(project, env) -> dict of variables.
        write_env: Callable(project, env, variables) -> None.
        dry_run: If True, compute result but do not persist changes.

    Returns:
        PruneResult describing which keys were removed / retained.

    Raises:
        PruneError: If source and reference are the same, or reference is empty.
    """
    if environment == reference_environment:
        raise PruneError(
            f"environment and reference_environment must differ; both are '{environment}'"
        )

    ref_vars = read_env(project, reference_environment)
    if not ref_vars:
        raise PruneError(
            f"Reference environment '{reference_environment}' in project '{project}' is empty."
        )

    target_vars = read_env(project, environment)
    allowed_keys = set(ref_vars.keys())

    removed: List[str] = []
    retained: Dict[str, str] = {}

    for key, value in target_vars.items():
        if key in allowed_keys:
            retained[key] = value
        else:
            removed.append(key)

    if removed and not dry_run:
        write_env(project, environment, retained)

    return PruneResult(
        project=project,
        environment=environment,
        reference_environment=reference_environment,
        removed_keys=removed,
        retained_keys=list(retained.keys()),
    )
