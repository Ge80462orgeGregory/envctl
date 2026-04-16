from __future__ import annotations
from dataclasses import dataclass
from typing import Callable


class CountError(Exception):
    pass


@dataclass
class CountResult:
    project: str
    environment: str
    total: int
    non_empty: int
    empty: int

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "environment": self.environment,
            "total": self.total,
            "non_empty": self.non_empty,
            "empty": self.empty,
        }


def count_env(
    project: str,
    environment: str,
    read_env: Callable[[str, str], dict[str, str]],
) -> CountResult:
    if not project:
        raise CountError("project name must not be empty")
    if not environment:
        raise CountError("environment name must not be empty")

    variables = read_env(project, environment)
    total = len(variables)
    non_empty = sum(1 for v in variables.values() if v.strip() != "")
    empty = total - non_empty

    return CountResult(
        project=project,
        environment=environment,
        total=total,
        non_empty=non_empty,
        empty=empty,
    )
