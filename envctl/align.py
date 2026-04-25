"""Align: pad or truncate all values in an environment to a fixed width."""

from dataclasses import dataclass, field
from typing import Dict, Optional


class AlignError(Exception):
    pass


@dataclass
class AlignResult:
    project: str
    environment: str
    original: Dict[str, str]
    aligned: Dict[str, str]
    total_changed: int

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "environment": self.environment,
            "total_changed": self.total_changed,
            "aligned": self.aligned,
        }


def align_env(
    project: str,
    environment: str,
    width: int,
    fill_char: str = " ",
    truncate: bool = False,
    read_env=None,
    write_env=None,
) -> AlignResult:
    """Pad or truncate all values to exactly `width` characters."""
    if read_env is None:
        from envctl.env_store import read_env as _read
        read_env = _read
    if write_env is None:
        from envctl.env_store import write_env as _write
        write_env = _write

    if width < 1:
        raise AlignError(f"width must be >= 1, got {width}")
    if len(fill_char) != 1:
        raise AlignError("fill_char must be exactly one character")

    original = read_env(project, environment)
    if not original:
        raise AlignError(f"No environment '{environment}' found for project '{project}'")

    aligned: Dict[str, str] = {}
    changed = 0

    for key, value in original.items():
        if len(value) < width:
            new_val = value.ljust(width, fill_char)
        elif len(value) > width and truncate:
            new_val = value[:width]
        else:
            new_val = value

        aligned[key] = new_val
        if new_val != value:
            changed += 1

    write_env(project, environment, aligned)

    return AlignResult(
        project=project,
        environment=environment,
        original=original,
        aligned=aligned,
        total_changed=changed,
    )
