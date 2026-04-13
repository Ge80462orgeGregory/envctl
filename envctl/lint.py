"""Lint environment variables for naming convention and value quality issues."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


@dataclass
class LintIssue:
    key: str
    message: str
    severity: str  # "error" | "warning" | "info"

    def to_dict(self) -> dict:
        return {"key": self.key, "message": self.message, "severity": self.severity}


@dataclass
class LintResult:
    project: str
    environment: str
    issues: list[LintIssue] = field(default_factory=list)

    @property
    def errors(self) -> list[LintIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> list[LintIssue]:
        return [i for i in self.issues if i.severity == "warning"]

    @property
    def passed(self) -> bool:
        return len(self.errors) == 0

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "environment": self.environment,
            "passed": self.passed,
            "issues": [i.to_dict() for i in self.issues],
        }


class LintError(Exception):
    pass


_RULES: list[Callable[[str, str], LintIssue | None]] = []


def _rule(fn: Callable[[str, str], LintIssue | None]):
    _RULES.append(fn)
    return fn


@_rule
def _check_uppercase(key: str, value: str) -> LintIssue | None:
    if key != key.upper():
        return LintIssue(key, "Key should be UPPER_SNAKE_CASE", "warning")
    return None


@_rule
def _check_no_spaces_in_key(key: str, value: str) -> LintIssue | None:
    if " " in key:
        return LintIssue(key, "Key must not contain spaces", "error")
    return None


@_rule
def _check_no_empty_value(key: str, value: str) -> LintIssue | None:
    if value.strip() == "":
        return LintIssue(key, "Value is empty", "warning")
    return None


@_rule
def _check_no_whitespace_padding(key: str, value: str) -> LintIssue | None:
    if value != value.strip():
        return LintIssue(key, "Value has leading or trailing whitespace", "warning")
    return None


@_rule
def _check_no_inline_newline(key: str, value: str) -> LintIssue | None:
    if "\n" in value or "\r" in value:
        return LintIssue(key, "Value contains a newline character", "error")
    return None


def lint_env(
    project: str,
    environment: str,
    read_env: Callable[[str, str], dict[str, str]],
) -> LintResult:
    variables = read_env(project, environment)
    if not variables and not isinstance(variables, dict):
        raise LintError(f"Could not read env '{environment}' for project '{project}'")

    result = LintResult(project=project, environment=environment)
    for key, value in variables.items():
        for rule in _RULES:
            issue = rule(key, value)
            if issue is not None:
                result.issues.append(issue)
    return result
