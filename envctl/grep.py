"""Search for keys or values matching a pattern within an environment."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable
import re


@dataclass
class GrepMatch:
    key: str
    value: str
    matched_on: str  # 'key', 'value', or 'both'

    def to_dict(self) -> dict:
        return {"key": self.key, "value": self.value, "matched_on": self.matched_on}


@dataclass
class GrepResult:
    project: str
    environment: str
    pattern: str
    matches: list[GrepMatch] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.matches)

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "environment": self.environment,
            "pattern": self.pattern,
            "total": self.total,
            "matches": [m.to_dict() for m in self.matches],
        }


class GrepError(Exception):
    pass


def grep_env(
    project: str,
    environment: str,
    pattern: str,
    *,
    read: Callable[[str, str], dict[str, str]],
    search_keys: bool = True,
    search_values: bool = True,
    ignore_case: bool = False,
) -> GrepResult:
    """Find keys/values in an environment matching *pattern* (regex)."""
    if not search_keys and not search_values:
        raise GrepError("At least one of search_keys or search_values must be True.")

    flags = re.IGNORECASE if ignore_case else 0
    try:
        regex = re.compile(pattern, flags)
    except re.error as exc:
        raise GrepError(f"Invalid pattern {pattern!r}: {exc}") from exc

    variables = read(project, environment)
    result = GrepResult(project=project, environment=environment, pattern=pattern)

    for key, value in variables.items():
        hit_key = search_keys and bool(regex.search(key))
        hit_val = search_values and bool(regex.search(value))
        if hit_key and hit_val:
            matched_on = "both"
        elif hit_key:
            matched_on = "key"
        elif hit_val:
            matched_on = "value"
        else:
            continue
        result.matches.append(GrepMatch(key=key, value=value, matched_on=matched_on))

    return result
