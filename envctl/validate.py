"""Validation logic for environment variable sets."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ValidationIssue:
    key: str
    message: str
    severity: str = "error"  # "error" | "warning"


@dataclass
class ValidationResult:
    project: str
    environment: str
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return not any(i.severity == "error" for i in self.issues)

    @property
    def errors(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "warning"]


class ValidateError(Exception):
    pass


_INVALID_KEY_CHARS = set(" \t\n=")


def _check_key(key: str) -> Optional[str]:
    if not key:
        return "Key must not be empty"
    if not key[0].isalpha() and key[0] != "_":
        return f"Key '{key}' must start with a letter or underscore"
    if any(c in _INVALID_KEY_CHARS for c in key):
        return f"Key '{key}' contains invalid characters"
    return None


def validate_env(
    project: str,
    environment: str,
    variables: Dict[str, str],
    required_keys: Optional[List[str]] = None,
) -> ValidationResult:
    """Validate an environment variable set and return a ValidationResult."""
    result = ValidationResult(project=project, environment=environment)

    for key, value in variables.items():
        msg = _check_key(key)
        if msg:
            result.issues.append(ValidationIssue(key=key, message=msg, severity="error"))
        if value == "":
            result.issues.append(
                ValidationIssue(key=key, message=f"Key '{key}' has an empty value", severity="warning")
            )

    if required_keys:
        for rk in required_keys:
            if rk not in variables:
                result.issues.append(
                    ValidationIssue(
                        key=rk,
                        message=f"Required key '{rk}' is missing",
                        severity="error",
                    )
                )

    return result
