"""Tag environments with arbitrary labels for grouping and filtering."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from envctl.env_store import read_env, write_env

_TAGS_KEY = "__envctl_tags__"


class TagError(Exception):
    """Raised when a tagging operation fails."""


@dataclass
class TagResult:
    project: str
    environment: str
    tags: List[str] = field(default_factory=list)


def _get_tags(data: Dict[str, str]) -> List[str]:
    raw = data.get(_TAGS_KEY, "")
    return [t for t in raw.split(",") if t] if raw else []


def _set_tags(data: Dict[str, str], tags: List[str]) -> Dict[str, str]:
    updated = dict(data)
    if tags:
        updated[_TAGS_KEY] = ",".join(sorted(set(tags)))
    else:
        updated.pop(_TAGS_KEY, None)
    return updated


def add_tags(
    project: str,
    environment: str,
    tags: List[str],
    *,
    read_fn=read_env,
    write_fn=write_env,
) -> TagResult:
    if not tags:
        raise TagError("No tags provided.")
    data = read_fn(project, environment)
    current = _get_tags(data)
    merged = sorted(set(current) | set(tags))
    write_fn(project, environment, _set_tags(data, merged))
    return TagResult(project=project, environment=environment, tags=merged)


def remove_tags(
    project: str,
    environment: str,
    tags: List[str],
    *,
    read_fn=read_env,
    write_fn=write_env,
) -> TagResult:
    if not tags:
        raise TagError("No tags provided.")
    data = read_fn(project, environment)
    current = set(_get_tags(data))
    remaining = sorted(current - set(tags))
    write_fn(project, environment, _set_tags(data, remaining))
    return TagResult(project=project, environment=environment, tags=remaining)


def list_tags(
    project: str,
    environment: str,
    *,
    read_fn=read_env,
) -> TagResult:
    data = read_fn(project, environment)
    return TagResult(project=project, environment=environment, tags=_get_tags(data))
