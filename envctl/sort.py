"""Sort environment variable keys within an env, with optional ordering strategies."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


class SortError(Exception):
    """Raised when sorting fails."""


@dataclass
class SortResult:
    project: str
    environment: str
    original_order: List[str]
    sorted_order: List[str]
    changed: bool

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "environment": self.environment,
            "original_order": self.original_order,
            "sorted_order": self.sorted_order,
            "changed": self.changed,
        }


def _alphabetical(keys: List[str]) -> List[str]:
    return sorted(keys)


def _reverse_alphabetical(keys: List[str]) -> List[str]:
    return sorted(keys, reverse=True)


def _by_length(keys: List[str]) -> List[str]:
    return sorted(keys, key=len)


_STRATEGIES: Dict[str, Callable[[List[str]], List[str]]] = {
    "alpha": _alphabetical,
    "reverse": _reverse_alphabetical,
    "length": _by_length,
}


def sort_env(
    project: str,
    environment: str,
    *,
    strategy: str = "alpha",
    read_env: Callable,
    write_env: Callable,
) -> SortResult:
    """Sort keys in *environment* of *project* using *strategy*.

    Args:
        project: Project name.
        environment: Environment name.
        strategy: One of 'alpha', 'reverse', 'length'.
        read_env: Callable(project, environment) -> dict[str, str].
        write_env: Callable(project, environment, dict[str, str]) -> None.

    Returns:
        SortResult describing what changed.

    Raises:
        SortError: If an unknown strategy is requested or the env is missing.
    """
    if strategy not in _STRATEGIES:
        raise SortError(
            f"Unknown sort strategy '{strategy}'. "
            f"Valid options: {', '.join(_STRATEGIES)}"
        )

    data: Dict[str, str] = read_env(project, environment)
    if not data:
        raise SortError(
            f"Environment '{environment}' in project '{project}' is empty or does not exist."
        )

    original_order = list(data.keys())
    sort_fn = _STRATEGIES[strategy]
    sorted_keys = sort_fn(original_order)

    changed = sorted_keys != original_order
    if changed:
        sorted_data = {k: data[k] for k in sorted_keys}
        write_env(project, environment, sorted_data)

    return SortResult(
        project=project,
        environment=environment,
        original_order=original_order,
        sorted_order=sorted_keys,
        changed=changed,
    )
