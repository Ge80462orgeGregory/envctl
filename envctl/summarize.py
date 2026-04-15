"""Summarize an environment: key count, value lengths, empty keys, and top-level stats."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List


class SummarizeError(Exception):
    pass


@dataclass
class SummaryResult:
    project: str
    environment: str
    total_keys: int
    empty_values: int
    non_empty_values: int
    avg_value_length: float
    longest_key: str
    shortest_key: str
    keys: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "project": self.project,
            "environment": self.environment,
            "total_keys": self.total_keys,
            "empty_values": self.empty_values,
            "non_empty_values": self.non_empty_values,
            "avg_value_length": round(self.avg_value_length, 2),
            "longest_key": self.longest_key,
            "shortest_key": self.shortest_key,
        }


def summarize_env(
    project: str,
    environment: str,
    read_env: Callable[[str, str], Dict[str, str]],
) -> SummaryResult:
    """Compute a summary of the given project/environment."""
    variables = read_env(project, environment)

    if not variables:
        raise SummarizeError(
            f"No variables found for '{project}/{environment}'."
        )

    keys = list(variables.keys())
    values = list(variables.values())

    empty_values = sum(1 for v in values if v == "")
    non_empty_values = len(values) - empty_values
    total_length = sum(len(v) for v in values)
    avg_value_length = total_length / len(values) if values else 0.0
    longest_key = max(keys, key=len) if keys else ""
    shortest_key = min(keys, key=len) if keys else ""

    return SummaryResult(
        project=project,
        environment=environment,
        total_keys=len(keys),
        empty_values=empty_values,
        non_empty_values=non_empty_values,
        avg_value_length=avg_value_length,
        longest_key=longest_key,
        shortest_key=shortest_key,
        keys=keys,
    )
