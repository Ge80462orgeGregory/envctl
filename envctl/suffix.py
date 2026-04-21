"""Add or strip a suffix from all keys in an environment."""

from dataclasses import dataclass, field
from typing import Dict, List

from envctl.env_store import read_env, write_env


class SuffixError(Exception):
    pass


@dataclass
class SuffixResult:
    project: str
    environment: str
    suffix: str
    changed: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    @property
    def total_changed(self) -> int:
        return len(self.changed)

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "environment": self.environment,
            "suffix": self.suffix,
            "changed": self.changed,
            "skipped": self.skipped,
            "total_changed": self.total_changed,
        }


def add_suffix(
    project: str,
    environment: str,
    suffix: str,
    read_fn=None,
    write_fn=None,
) -> SuffixResult:
    if not suffix:
        raise SuffixError("Suffix must not be empty.")

    _read = read_fn or read_env
    _write = write_fn or write_env

    env: Dict[str, str] = _read(project, environment)
    if not env:
        raise SuffixError(f"Environment '{environment}' in project '{project}' is empty or does not exist.")

    result = SuffixResult(project=project, environment=environment, suffix=suffix)
    new_env: Dict[str, str] = {}

    for key, value in env.items():
        new_key = f"{key}{suffix}"
        if new_key in env:
            result.skipped.append(key)
            new_env[key] = value
        else:
            result.changed.append(key)
            new_env[new_key] = value

    _write(project, environment, new_env)
    return result


def strip_suffix(
    project: str,
    environment: str,
    suffix: str,
    read_fn=None,
    write_fn=None,
) -> SuffixResult:
    if not suffix:
        raise SuffixError("Suffix must not be empty.")

    _read = read_fn or read_env
    _write = write_fn or write_env

    env: Dict[str, str] = _read(project, environment)
    if not env:
        raise SuffixError(f"Environment '{environment}' in project '{project}' is empty or does not exist.")

    result = SuffixResult(project=project, environment=environment, suffix=suffix)
    new_env: Dict[str, str] = {}

    for key, value in env.items():
        if key.endswith(suffix):
            new_key = key[: -len(suffix)]
            result.changed.append(key)
            new_env[new_key] = value
        else:
            result.skipped.append(key)
            new_env[key] = value

    _write(project, environment, new_env)
    return result
