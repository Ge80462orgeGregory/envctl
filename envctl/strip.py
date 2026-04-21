"""Strip leading/trailing whitespace from env variable values."""

from dataclasses import dataclass, field
from typing import Callable, Dict, List


class StripError(Exception):
    pass


@dataclass
class StripResult:
    project: str
    environment: str
    stripped: List[str] = field(default_factory=list)
    unchanged: List[str] = field(default_factory=list)

    @property
    def total_stripped(self) -> int:
        return len(self.stripped)

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "environment": self.environment,
            "stripped": self.stripped,
            "unchanged": self.unchanged,
            "total_stripped": self.total_stripped,
        }


def strip_env(
    project: str,
    environment: str,
    read_env: Callable[[str, str], Dict[str, str]],
    write_env: Callable[[str, str, Dict[str, str]], None],
    keys: List[str] = None,
) -> StripResult:
    """Strip whitespace from values in the given environment.

    Args:
        project: Project name.
        environment: Environment name.
        read_env: Callable to read env variables.
        write_env: Callable to persist env variables.
        keys: Optional list of keys to restrict stripping to.

    Returns:
        StripResult describing which keys were changed.

    Raises:
        StripError: If the environment cannot be read or written.
    """
    try:
        data = read_env(project, environment)
    except Exception as exc:
        raise StripError(f"Failed to read env '{project}/{environment}': {exc}") from exc

    if not data:
        raise StripError(f"Environment '{project}/{environment}' is empty or does not exist.")

    target_keys = keys if keys else list(data.keys())
    result = StripResult(project=project, environment=environment)
    updated = dict(data)

    for key in target_keys:
        if key not in data:
            continue
        original = data[key]
        stripped = original.strip()
        if stripped != original:
            updated[key] = stripped
            result.stripped.append(key)
        else:
            result.unchanged.append(key)

    try:
        write_env(project, environment, updated)
    except Exception as exc:
        raise StripError(f"Failed to write env '{project}/{environment}': {exc}") from exc

    return result
