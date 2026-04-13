"""Protect (write-protect) specific keys in an environment, preventing accidental overwrites."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


class ProtectError(Exception):
    pass


@dataclass
class ProtectResult:
    project: str
    environment: str
    newly_protected: List[str] = field(default_factory=list)
    already_protected: List[str] = field(default_factory=list)
    newly_unprotected: List[str] = field(default_factory=list)
    not_found: List[str] = field(default_factory=list)


_PROTECTED_META_KEY = "__envctl_protected__"


def _get_protected(read: Callable) -> List[str]:
    data = read(_PROTECTED_META_KEY.replace("__envctl_", "").replace("__", ""))
    env = read.__self__ if hasattr(read, "__self__") else None  # noqa
    # We store protected list inside the env vars under a sentinel key
    return []


def _load_protected(env: Dict[str, str]) -> List[str]:
    raw = env.get(_PROTECTED_META_KEY, "")
    return [k.strip() for k in raw.split(",") if k.strip()]


def _save_protected(env: Dict[str, str], keys: List[str]) -> Dict[str, str]:
    updated = dict(env)
    if keys:
        updated[_PROTECTED_META_KEY] = ",".join(sorted(set(keys)))
    else:
        updated.pop(_PROTECTED_META_KEY, None)
    return updated


def protect_keys(
    project: str,
    environment: str,
    keys: List[str],
    read: Callable[[str, str], Dict[str, str]],
    write: Callable[[str, str, Dict[str, str]], None],
) -> ProtectResult:
    if not project or not environment:
        raise ProtectError("project and environment must not be empty")
    if not keys:
        raise ProtectError("at least one key must be specified")

    env = read(project, environment)
    protected = _load_protected(env)
    result = ProtectResult(project=project, environment=environment)

    for key in keys:
        if key == _PROTECTED_META_KEY:
            continue
        if key not in env and key not in protected:
            result.not_found.append(key)
        elif key in protected:
            result.already_protected.append(key)
        else:
            protected.append(key)
            result.newly_protected.append(key)

    updated = _save_protected(env, protected)
    write(project, environment, updated)
    return result


def unprotect_keys(
    project: str,
    environment: str,
    keys: List[str],
    read: Callable[[str, str], Dict[str, str]],
    write: Callable[[str, str, Dict[str, str]], None],
) -> ProtectResult:
    if not project or not environment:
        raise ProtectError("project and environment must not be empty")
    if not keys:
        raise ProtectError("at least one key must be specified")

    env = read(project, environment)
    protected = _load_protected(env)
    result = ProtectResult(project=project, environment=environment)

    for key in keys:
        if key in protected:
            protected.remove(key)
            result.newly_unprotected.append(key)
        else:
            result.not_found.append(key)

    updated = _save_protected(env, protected)
    write(project, environment, updated)
    return result


def is_protected(key: str, env: Dict[str, str]) -> bool:
    return key in _load_protected(env)
