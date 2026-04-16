from dataclasses import dataclass
from typing import Dict, Optional


class TruncateError(Exception):
    pass


@dataclass
class TruncateResult:
    project: str
    environment: str
    total_truncated: int
    changes: Dict[str, str]  # key -> truncated value

    def to_dict(self):
        return {
            "project": self.project,
            "environment": self.environment,
            "total_truncated": self.total_truncated,
            "changes": self.changes,
        }


def truncate_env(
    project: str,
    environment: str,
    max_length: int,
    keys: Optional[list] = None,
    read_env=None,
    write_env=None,
) -> TruncateResult:
    if max_length < 1:
        raise TruncateError("max_length must be at least 1")

    env = read_env(project, environment)
    if not env:
        raise TruncateError(f"Environment '{environment}' in project '{project}' is empty or does not exist")

    updated = dict(env)
    changes = {}

    target_keys = keys if keys else list(env.keys())

    for key in target_keys:
        if key not in env:
            continue
        val = env[key]
        if len(val) > max_length:
            truncated = val[:max_length]
            updated[key] = truncated
            changes[key] = truncated

    if changes:
        write_env(project, environment, updated)

    return TruncateResult(
        project=project,
        environment=environment,
        total_truncated=len(changes),
        changes=changes,
    )
