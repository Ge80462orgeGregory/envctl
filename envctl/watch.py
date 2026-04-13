"""Watch an environment for changes and report diffs."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from envctl.env_store import read_env, write_env
from envctl.diff import diff_envs, format_diff


class WatchError(Exception):
    """Raised when a watch operation fails."""


@dataclass
class WatchSnapshot:
    project: str
    environment: str
    variables: Dict[str, str]


@dataclass
class WatchResult:
    project: str
    environment: str
    before: Dict[str, str]
    after: Dict[str, str]
    diff_lines: List[str] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.diff_lines)


def take_watch_snapshot(
    project: str,
    environment: str,
    read: Callable[[str, str], Dict[str, str]] = read_env,
) -> WatchSnapshot:
    """Capture the current state of an environment."""
    if not project or not environment:
        raise WatchError("project and environment must not be empty")
    variables = read(project, environment)
    return WatchSnapshot(project=project, environment=environment, variables=dict(variables))


def compare_watch_snapshot(
    snapshot: WatchSnapshot,
    read: Callable[[str, str], Dict[str, str]] = read_env,
) -> WatchResult:
    """Compare a snapshot against the current state and return a diff."""
    current = read(snapshot.project, snapshot.environment)
    diff = diff_envs(snapshot.variables, current)
    lines = format_diff(diff)
    return WatchResult(
        project=snapshot.project,
        environment=snapshot.environment,
        before=snapshot.variables,
        after=dict(current),
        diff_lines=lines,
    )
