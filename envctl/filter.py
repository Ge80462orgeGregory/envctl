from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


class FilterError(Exception):
    pass


@dataclass
class FilterResult:
    project: str
    environment: str
    matched: Dict[str, str] = field(default_factory=dict)
    total_scanned: int = 0

    def total_matched(self) -> int:
        return len(self.matched)

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "environment": self.environment,
            "matched": self.matched,
            "total_scanned": self.total_scanned,
            "total_matched": self.total_matched(),
        }


def filter_env(
    project: str,
    environment: str,
    read_env: Callable[[str, str], Dict[str, str]],
    prefix: Optional[str] = None,
    suffix: Optional[str] = None,
    contains: Optional[str] = None,
    value_contains: Optional[str] = None,
    invert: bool = False,
) -> FilterResult:
    if not project:
        raise FilterError("Project name must not be empty.")
    if not environment:
        raise FilterError("Environment name must not be empty.")

    env = read_env(project, environment)
    matched = {}

    for key, value in env.items():
        match = True
        if prefix and not key.startswith(prefix):
            match = False
        if suffix and not key.endswith(suffix):
            match = False
        if contains and contains not in key:
            match = False
        if value_contains and value_contains not in value:
            match = False
        if invert:
            match = not match
        if match:
            matched[key] = value

    return FilterResult(
        project=project,
        environment=environment,
        matched=matched,
        total_scanned=len(env),
    )
