"""Inspect an environment: surface metadata and key-level detail in one pass."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


@dataclass
class KeyDetail:
    key: str
    value: str
    has_placeholder: bool
    is_empty: bool
    length: int

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "value": self.value,
            "has_placeholder": self.has_placeholder,
            "is_empty": self.is_empty,
            "length": self.length,
        }


@dataclass
class InspectResult:
    project: str
    environment: str
    total_keys: int
    empty_keys: int
    placeholder_keys: int
    keys: List[KeyDetail] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "environment": self.environment,
            "total_keys": self.total_keys,
            "empty_keys": self.empty_keys,
            "placeholder_keys": self.placeholder_keys,
            "keys": [k.to_dict() for k in self.keys],
        }


class InspectError(Exception):
    pass


_PLACEHOLDER_MARKERS = ("${{", "{{", "${", "__PLACEHOLDER__")


def _has_placeholder(value: str) -> bool:
    return any(marker in value for marker in _PLACEHOLDER_MARKERS)


def inspect_env(
    project: str,
    environment: str,
    read_env: Callable[[str, str], Dict[str, str]],
) -> InspectResult:
    """Read *project/environment* and return a rich InspectResult."""
    variables = read_env(project, environment)
    if not variables and variables is None:
        raise InspectError(f"Environment '{environment}' not found in project '{project}'.")

    keys: List[KeyDetail] = []
    for k, v in sorted(variables.items()):
        keys.append(
            KeyDetail(
                key=k,
                value=v,
                has_placeholder=_has_placeholder(v),
                is_empty=(v.strip() == ""),
                length=len(v),
            )
        )

    return InspectResult(
        project=project,
        environment=environment,
        total_keys=len(keys),
        empty_keys=sum(1 for k in keys if k.is_empty),
        placeholder_keys=sum(1 for k in keys if k.has_placeholder),
        keys=keys,
    )
