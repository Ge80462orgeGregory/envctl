"""cast.py — Type-cast environment variable values within an env set."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


class CastError(Exception):
    """Raised when a cast operation fails."""


@dataclass
class CastResult:
    project: str
    environment: str
    cast: Dict[str, str] = field(default_factory=dict)   # key -> new string value
    skipped: List[str] = field(default_factory=list)      # keys not found
    errors: List[str] = field(default_factory=list)       # keys that failed conversion

    @property
    def total_cast(self) -> int:
        return len(self.cast)

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "environment": self.environment,
            "cast": self.cast,
            "skipped": self.skipped,
            "errors": self.errors,
            "total_cast": self.total_cast,
        }


_CASTERS: Dict[str, Callable[[str], str]] = {
    "int": lambda v: str(int(v)),
    "float": lambda v: str(float(v)),
    "bool": lambda v: str(bool(v.strip().lower() not in ("", "0", "false", "no", "off"))),
    "str": lambda v: str(v),
    "upper": lambda v: v.upper(),
    "lower": lambda v: v.lower(),
    "strip": lambda v: v.strip(),
}


def cast_env(
    project: str,
    environment: str,
    casts: Dict[str, str],          # {key: type_name}
    read_fn: Callable,
    write_fn: Callable,
) -> CastResult:
    """Apply type casts to specific keys in an environment.

    Args:
        project: project name.
        environment: environment name.
        casts: mapping of key -> cast type (e.g. {"PORT": "int"}).
        read_fn: callable(project, env) -> dict.
        write_fn: callable(project, env, dict) -> None.

    Returns:
        CastResult summarising what changed.
    """
    data = read_fn(project, environment)
    result = CastResult(project=project, environment=environment)

    for key, type_name in casts.items():
        if key not in data:
            result.skipped.append(key)
            continue
        caster = _CASTERS.get(type_name)
        if caster is None:
            raise CastError(f"Unknown cast type '{type_name}'. "
                            f"Valid types: {sorted(_CASTERS)}")
        try:
            new_val = caster(data[key])
            data[key] = new_val
            result.cast[key] = new_val
        except (ValueError, TypeError) as exc:
            result.errors.append(f"{key}: {exc}")

    if result.cast:
        write_fn(project, environment, data)

    return result
