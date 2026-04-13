"""Compute and verify checksums for environment variable sets."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Callable


class ChecksumError(Exception):
    """Raised when a checksum operation fails."""


@dataclass
class ChecksumResult:
    project: str
    environment: str
    checksum: str
    key_count: int

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "environment": self.environment,
            "checksum": self.checksum,
            "key_count": self.key_count,
        }


@dataclass
class VerifyResult:
    project: str
    environment: str
    expected: str
    actual: str
    matched: bool

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "environment": self.environment,
            "expected": self.expected,
            "actual": self.actual,
            "matched": self.matched,
        }


def _compute(variables: dict[str, str]) -> str:
    """Compute a stable SHA-256 checksum over sorted key-value pairs."""
    stable = json.dumps(dict(sorted(variables.items())), sort_keys=True)
    return hashlib.sha256(stable.encode()).hexdigest()


def compute_checksum(
    project: str,
    environment: str,
    read_env: Callable[[str, str], dict[str, str]],
) -> ChecksumResult:
    """Compute the checksum of an environment."""
    variables = read_env(project, environment)
    if not isinstance(variables, dict):
        raise ChecksumError(
            f"Could not read environment '{environment}' for project '{project}'."
        )
    checksum = _compute(variables)
    return ChecksumResult(
        project=project,
        environment=environment,
        checksum=checksum,
        key_count=len(variables),
    )


def verify_checksum(
    project: str,
    environment: str,
    expected: str,
    read_env: Callable[[str, str], dict[str, str]],
) -> VerifyResult:
    """Verify that the current checksum matches the expected value."""
    result = compute_checksum(project, environment, read_env)
    return VerifyResult(
        project=project,
        environment=environment,
        expected=expected,
        actual=result.checksum,
        matched=result.checksum == expected,
    )
