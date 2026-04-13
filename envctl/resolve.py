"""Resolve placeholder references between environments.

Allows one environment's values to reference another environment's keys
using the syntax ${ENV:KEY}, e.g. ${staging:DATABASE_URL}.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable

REF_PATTERN = re.compile(r"\$\{([^}:]+):([^}]+)\}")


class ResolveError(Exception):
    pass


@dataclass
class ResolveResult:
    resolved: dict[str, str] = field(default_factory=dict)
    substitutions: list[tuple[str, str, str]] = field(default_factory=list)  # (key, ref, value)
    unresolved: list[tuple[str, str]] = field(default_factory=list)  # (key, ref)

    @property
    def total_substitutions(self) -> int:
        return len(self.substitutions)

    @property
    def total_unresolved(self) -> int:
        return len(self.unresolved)


def resolve_env(
    project: str,
    environment: str,
    read_env: Callable[[str, str], dict[str, str]],
    strict: bool = False,
) -> ResolveResult:
    """Resolve cross-environment references in *environment* for *project*.

    Args:
        project: Project name.
        environment: Target environment whose values are resolved.
        read_env: Callable(project, env) -> dict of variables.
        strict: If True, raise ResolveError on any unresolved reference.

    Returns:
        ResolveResult with resolved variable map and metadata.
    """
    variables = read_env(project, environment)
    if not variables:
        raise ResolveError(f"Environment '{environment}' not found in project '{project}'")

    result = ResolveResult()
    _cache: dict[str, dict[str, str]] = {}

    def _fetch(env: str) -> dict[str, str]:
        if env not in _cache:
            _cache[env] = read_env(project, env)
        return _cache[env]

    for key, value in variables.items():
        new_value = value
        for match in REF_PATTERN.finditer(value):
            ref_env, ref_key = match.group(1), match.group(2)
            source = _fetch(ref_env)
            if ref_key in source:
                replacement = source[ref_key]
                new_value = new_value.replace(match.group(0), replacement)
                result.substitutions.append((key, match.group(0), replacement))
            else:
                ref = match.group(0)
                result.unresolved.append((key, ref))
                if strict:
                    raise ResolveError(
                        f"Cannot resolve '{ref}' for key '{key}': "
                        f"key '{ref_key}' not found in environment '{ref_env}'"
                    )
        result.resolved[key] = new_value

    return result
