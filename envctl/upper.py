from typing import Callable
from dataclasses import dataclass


class UpperError(Exception):
    pass


@dataclass
class UpperResult:
    project: str
    environment: str
    total_keys: int
    total_changed: int
    changed_keys: list

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "environment": self.environment,
            "total_keys": self.total_keys,
            "total_changed": self.total_changed,
            "changed_keys": self.changed_keys,
        }


def upper_env(
    project: str,
    environment: str,
    read_env: Callable,
    write_env: Callable,
    keys: list = None,
    dry_run: bool = False,
) -> UpperResult:
    """Convert env variable values to uppercase."""
    env = read_env(project, environment)
    if env is None:
        raise UpperError(f"Environment '{environment}' not found in project '{project}'")

    changed_keys = []
    updated = dict(env)

    for key, value in env.items():
        if keys and key not in keys:
            continue
        new_value = value.upper()
        if new_value != value:
            updated[key] = new_value
            changed_keys.append(key)

    if not dry_run and changed_keys:
        write_env(project, environment, updated)

    return UpperResult(
        project=project,
        environment=environment,
        total_keys=len(env),
        total_changed=len(changed_keys),
        changed_keys=sorted(changed_keys),
    )
