"""Mask sensitive environment variable values for safe display."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

DEFAULT_SENSITIVE_PATTERNS = [
    "secret", "password", "passwd", "token", "api_key", "apikey",
    "auth", "credential", "private_key", "access_key", "signing",
]

MASK_CHAR = "*"
VISIBLE_CHARS = 4


class MaskError(Exception):
    pass


@dataclass
class MaskResult:
    original: Dict[str, str]
    masked: Dict[str, str]
    masked_keys: List[str] = field(default_factory=list)

    @property
    def total_masked(self) -> int:
        return len(self.masked_keys)


def _is_sensitive(key: str, patterns: List[str]) -> bool:
    lower = key.lower()
    return any(p in lower for p in patterns)


def _mask_value(value: str, visible: int = VISIBLE_CHARS) -> str:
    if not value:
        return value
    if len(value) <= visible:
        return MASK_CHAR * len(value)
    return value[:visible] + MASK_CHAR * (len(value) - visible)


def mask_env(
    env: Dict[str, str],
    patterns: Optional[List[str]] = None,
    extra_keys: Optional[List[str]] = None,
    visible_chars: int = VISIBLE_CHARS,
) -> MaskResult:
    """Return a MaskResult with sensitive values obscured.

    Args:
        env: The environment variables dict to process.
        patterns: Key substring patterns that indicate sensitivity.
                  Defaults to DEFAULT_SENSITIVE_PATTERNS.
        extra_keys: Additional exact key names to always mask.
        visible_chars: Number of leading characters to keep visible.
    """
    if patterns is None:
        patterns = DEFAULT_SENSITIVE_PATTERNS
    extra_keys = set(k.upper() for k in (extra_keys or []))

    masked: Dict[str, str] = {}
    masked_keys: List[str] = []

    for key, value in env.items():
        if _is_sensitive(key, patterns) or key.upper() in extra_keys:
            masked[key] = _mask_value(value, visible_chars)
            masked_keys.append(key)
        else:
            masked[key] = value

    return MaskResult(original=env, masked=masked, masked_keys=sorted(masked_keys))
