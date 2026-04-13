"""Lock and unlock environment variables to prevent accidental modification."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from envctl.env_store import read_env, write_env


LOCK_KEY = "__locked_keys__"


class LockError(Exception):
    pass


@dataclass
class LockResult:
    project: str
    environment: str
    locked: List[str] = field(default_factory=list)
    unlocked: List[str] = field(default_factory=list)
    already_locked: List[str] = field(default_factory=list)
    already_unlocked: List[str] = field(default_factory=list)


def _get_locked_keys(env: dict) -> List[str]:
    raw = env.get(LOCK_KEY, "")
    if not raw:
        return []
    return [k.strip() for k in raw.split(",") if k.strip()]


def _set_locked_keys(env: dict, keys: List[str]) -> dict:
    updated = dict(env)
    if keys:
        updated[LOCK_KEY] = ",".join(sorted(set(keys)))
    else:
        updated.pop(LOCK_KEY, None)
    return updated


def lock_keys(
    project: str,
    environment: str,
    keys: List[str],
    read_fn=read_env,
    write_fn=write_env,
) -> LockResult:
    env = read_fn(project, environment)
    missing = [k for k in keys if k not in env and k != LOCK_KEY]
    if missing:
        raise LockError(f"Keys not found in {project}/{environment}: {', '.join(missing)}")

    currently_locked = _get_locked_keys(env)
    result = LockResult(project=project, environment=environment)

    new_locked = list(currently_locked)
    for key in keys:
        if key in currently_locked:
            result.already_locked.append(key)
        else:
            new_locked.append(key)
            result.locked.append(key)

    updated = _set_locked_keys(env, new_locked)
    write_fn(project, environment, updated)
    return result


def unlock_keys(
    project: str,
    environment: str,
    keys: List[str],
    read_fn=read_env,
    write_fn=write_env,
) -> LockResult:
    env = read_fn(project, environment)
    currently_locked = _get_locked_keys(env)
    result = LockResult(project=project, environment=environment)

    new_locked = list(currently_locked)
    for key in keys:
        if key not in currently_locked:
            result.already_unlocked.append(key)
        else:
            new_locked.remove(key)
            result.unlocked.append(key)

    updated = _set_locked_keys(env, new_locked)
    write_fn(project, environment, updated)
    return result


def get_locked_keys(
    project: str,
    environment: str,
    read_fn=read_env,
) -> List[str]:
    env = read_fn(project, environment)
    return _get_locked_keys(env)
