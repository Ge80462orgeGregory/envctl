"""Redact sensitive values from an environment, replacing them with a placeholder."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from envctl.env_store import read_env, write_env

_DEFAULT_SENSITIVE_PATTERNS = (
    "secret",
    "password",
    "passwd",
    "token",
    "api_key",
    "apikey",
    "private_key",
    "auth",
    "credential",
    "cert",
)

DEFAULT_PLACEHOLDER = "**REDACTED**"


class RedactError(Exception):
    """Raised when redaction cannot be completed."""


@dataclass
class RedactResult:
    project: str
    environment: str
    redacted_keys: list[str] = field(default_factory=list)
    total_redacted: int = 0


def _is_sensitive(key: str, patterns: tuple[str, ...]) -> bool:
    lower = key.lower()
    return any(p in lower for p in patterns)


def redact_env(
    project: str,
    environment: str,
    *,
    keys: list[str] | None = None,
    placeholder: str = DEFAULT_PLACEHOLDER,
    patterns: tuple[str, ...] = _DEFAULT_SENSITIVE_PATTERNS,
    read: Callable = read_env,
    write: Callable = write_env,
) -> RedactResult:
    """Replace sensitive (or specified) values with *placeholder* in-place.

    Args:
        project: Project name.
        environment: Environment name.
        keys: Explicit list of keys to redact. When *None* all keys matching
              *patterns* are redacted automatically.
        placeholder: String to substitute for sensitive values.
        patterns: Substrings that mark a key as sensitive (case-insensitive).
        read: Injectable read_env callable (for testing).
        write: Injectable write_env callable (for testing).

    Returns:
        A :class:`RedactResult` describing what was changed.

    Raises:
        RedactError: If the environment does not exist.
    """
    current = read(project, environment)
    if not current:
        raise RedactError(
            f"Environment '{environment}' for project '{project}' not found or is empty."
        )

    updated = dict(current)
    redacted_keys: list[str] = []

    for k, v in current.items():
        should_redact = (keys is not None and k in keys) or (
            keys is None and _is_sensitive(k, patterns)
        )
        if should_redact and v != placeholder:
            updated[k] = placeholder
            redacted_keys.append(k)

    if redacted_keys:
        write(project, environment, updated)

    return RedactResult(
        project=project,
        environment=environment,
        redacted_keys=sorted(redacted_keys),
        total_redacted=len(redacted_keys),
    )
