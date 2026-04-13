"""Compare two environments across the same or different projects."""

from dataclasses import dataclass, field
from typing import Optional
from envctl.env_store import read_env


@dataclass
class CompareError(Exception):
    message: str

    def __str__(self) -> str:
        return self.message


@dataclass
class CompareResult:
    source_project: str
    source_env: str
    target_project: str
    target_env: str
    only_in_source: dict[str, str] = field(default_factory=dict)
    only_in_target: dict[str, str] = field(default_factory=dict)
    differing: dict[str, tuple[str, str]] = field(default_factory=dict)
    matching: dict[str, str] = field(default_factory=dict)

    @property
    def is_identical(self) -> bool:
        return (
            not self.only_in_source
            and not self.only_in_target
            and not self.differing
        )

    @property
    def total_differences(self) -> int:
        return len(self.only_in_source) + len(self.only_in_target) + len(self.differing)


def compare_envs(
    source_project: str,
    source_env: str,
    target_project: str,
    target_env: str,
    read=read_env,
) -> CompareResult:
    """Compare two environments and return a structured result."""
    src = read(source_project, source_env)
    tgt = read(target_project, target_env)

    if not src and not tgt:
        raise CompareError(
            f"Neither '{source_project}/{source_env}' nor "
            f"'{target_project}/{target_env}' contain any variables."
        )

    result = CompareResult(
        source_project=source_project,
        source_env=source_env,
        target_project=target_project,
        target_env=target_env,
    )

    all_keys = set(src) | set(tgt)
    for key in sorted(all_keys):
        in_src = key in src
        in_tgt = key in tgt
        if in_src and not in_tgt:
            result.only_in_source[key] = src[key]
        elif in_tgt and not in_src:
            result.only_in_target[key] = tgt[key]
        elif src[key] == tgt[key]:
            result.matching[key] = src[key]
        else:
            result.differing[key] = (src[key], tgt[key])

    return result
