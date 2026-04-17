"""Lowercase env values."""
from dataclasses import dataclass
from typing import Dict


class LowercaseError(Exception):
    pass


@dataclass
class LowercaseResult:
    project: str
    environment: str
    total_changed: int
    changes: Dict[str, str]  # key -> new value

    def to_dict(self):
        return {
            "project": self.project,
            "environment": self.environment,
            "total_changed": self.total_changed,
            "changes": self.changes,
        }


def lowercase_env(
    project: str,
    environment: str,
    read_env,
    write_env,
    keys: list = None,
) -> LowercaseResult:
    """Convert env values to lowercase. Optionally restrict to specific keys."""
    env = read_env(project, environment)
    if env is None:
        raise LowercaseError(f"Environment '{environment}' not found in project '{project}'")

    updated = dict(env)
    changes = {}

    for k, v in env.items():
        if keys and k not in keys:
            continue
        lowered = v.lower()
        if lowered != v:
            updated[k] = lowered
            changes[k] = lowered

    if changes:
        write_env(project, environment, updated)

    return LowercaseResult(
        project=project,
        environment=environment,
        total_changed=len(changes),
        changes=changes,
    )
