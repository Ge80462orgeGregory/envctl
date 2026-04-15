"""Annotate environment variable keys with human-readable descriptions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


class AnnotateError(Exception):
    pass


@dataclass
class AnnotateResult:
    project: str
    environment: str
    added: dict[str, str] = field(default_factory=dict)
    updated: dict[str, str] = field(default_factory=dict)
    removed: list[str] = field(default_factory=list)

    @property
    def total_changes(self) -> int:
        return len(self.added) + len(self.updated) + len(self.removed)

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "environment": self.environment,
            "added": self.added,
            "updated": self.updated,
            "removed": self.removed,
            "total_changes": self.total_changes,
        }


_ANNOTATION_KEY = "__annotations__"


def _get_annotations(read: Callable, project: str, environment: str) -> dict[str, str]:
    env = read(project, environment)
    raw = env.get(_ANNOTATION_KEY, "")
    if not raw:
        return {}
    result = {}
    for part in raw.split(","):
        part = part.strip()
        if "=" in part:
            k, _, v = part.partition("=")
            result[k.strip()] = v.strip()
    return result


def _set_annotations(
    read: Callable,
    write: Callable,
    project: str,
    environment: str,
    annotations: dict[str, str],
) -> None:
    env = read(project, environment)
    if annotations:
        env[_ANNOTATION_KEY] = ", ".join(f"{k}={v}" for k, v in sorted(annotations.items()))
    else:
        env.pop(_ANNOTATION_KEY, None)
    write(project, environment, env)


def annotate_env(
    read: Callable,
    write: Callable,
    project: str,
    environment: str,
    descriptions: dict[str, str],
    remove_keys: list[str] | None = None,
) -> AnnotateResult:
    """Add or update annotations for keys in an environment."""
    env = read(project, environment)
    if not env and not descriptions:
        raise AnnotateError(f"Environment '{project}/{environment}' is empty or does not exist.")

    existing = _get_annotations(read, project, environment)
    result = AnnotateResult(project=project, environment=environment)

    for key, desc in descriptions.items():
        if key not in env and key != _ANNOTATION_KEY:
            raise AnnotateError(f"Key '{key}' does not exist in '{project}/{environment}'.")
        if key in existing:
            if existing[key] != desc:
                result.updated[key] = desc
        else:
            result.added[key] = desc
        existing[key] = desc

    for key in (remove_keys or []):
        if key in existing:
            del existing[key]
            result.removed.append(key)

    _set_annotations(read, write, project, environment, existing)
    return result
