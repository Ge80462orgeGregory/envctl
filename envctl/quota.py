"""Quota enforcement: warn or error when an env exceeds a key-count limit."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


@dataclass
class QuotaError(Exception):
    message: str

    def __str__(self) -> str:  # pragma: no cover
        return self.message


@dataclass
class QuotaResult:
    project: str
    environment: str
    key_count: int
    limit: int
    exceeded: bool
    warning: bool

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "environment": self.environment,
            "key_count": self.key_count,
            "limit": self.limit,
            "exceeded": self.exceeded,
            "warning": self.warning,
        }


def check_quota(
    project: str,
    environment: str,
    limit: int,
    *,
    warn_at: float = 0.8,
    read_env: Callable[[str, str], dict[str, str]],
) -> QuotaResult:
    """Return a QuotaResult describing how close *project/environment* is to *limit*.

    Args:
        project:     Project name.
        environment: Environment name.
        limit:       Maximum number of keys allowed.
        warn_at:     Fraction of *limit* at which a warning is raised (default 80 %).
        read_env:    Callable ``(project, environment) -> dict`` used to load variables.

    Raises:
        QuotaError: If *limit* is not a positive integer.
    """
    if limit <= 0:
        raise QuotaError("limit must be a positive integer")
    if not (0.0 < warn_at <= 1.0):
        raise QuotaError("warn_at must be in the range (0, 1]")

    env = read_env(project, environment)
    key_count = len(env)
    exceeded = key_count > limit
    warning = not exceeded and key_count >= int(limit * warn_at)

    return QuotaResult(
        project=project,
        environment=environment,
        key_count=key_count,
        limit=limit,
        exceeded=exceeded,
        warning=warning,
    )
