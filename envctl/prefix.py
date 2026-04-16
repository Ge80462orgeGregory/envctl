"""Add or strip a prefix from all keys in an environment."""
from dataclasses import dataclass, field
from typing import Dict, List


class PrefixError(Exception):
    pass


@dataclass
class PrefixResult:
    project: str
    environment: str
    changed: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    @property
    def total_changed(self) -> int:
        return len(self.changed)

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "environment": self.environment,
            "changed": self.changed,
            "skipped": self.skipped,
            "total_changed": self.total_changed,
        }


def add_prefix(
    project: str,
    environment: str,
    prefix: str,
    read_env,
    write_env,
    overwrite: bool = False,
) -> PrefixResult:
    if not prefix:
        raise PrefixError("Prefix must not be empty.")

    data: Dict[str, str] = read_env(project, environment)
    if not data:
        raise PrefixError(f"Environment '{environment}' in project '{project}' is empty or does not exist.")

    result = PrefixResult(project=project, environment=environment)
    new_data: Dict[str, str] = {}

    for key, value in data.items():
        if key.startswith(prefix):
            result.skipped.append(key)
            new_data[key] = value
        else:
            new_key = f"{prefix}{key}"
            if new_key in data and not overwrite:
                result.skipped.append(key)
                new_data[key] = value
            else:
                result.changed.append(key)
                new_data[new_key] = value

    write_env(project, environment, new_data)
    return result


def strip_prefix(
    project: str,
    environment: str,
    prefix: str,
    read_env,
    write_env,
) -> PrefixResult:
    if not prefix:
        raise PrefixError("Prefix must not be empty.")

    data: Dict[str, str] = read_env(project, environment)
    if not data:
        raise PrefixError(f"Environment '{environment}' in project '{project}' is empty or does not exist.")

    result = PrefixResult(project=project, environment=environment)
    new_data: Dict[str, str] = {}

    for key, value in data.items():
        if key.startswith(prefix):
            new_key = key[len(prefix):]
            result.changed.append(key)
            new_data[new_key] = value
        else:
            result.skipped.append(key)
            new_data[key] = value

    write_env(project, environment, new_data)
    return result
