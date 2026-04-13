"""Tests for envctl.lint module."""

from __future__ import annotations

import pytest

from envctl.lint import LintIssue, LintResult, LintError, lint_env


def _make_read(data: dict[str, dict[str, dict[str, str]]]):
    def _read(project: str, environment: str) -> dict[str, str]:
        return data.get(project, {}).get(environment, {})
    return _read


def test_clean_env_has_no_issues():
    read = _make_read({"myapp": {"prod": {"DATABASE_URL": "postgres://localhost", "PORT": "5432"}}})
    result = lint_env("myapp", "prod", read)
    assert result.passed
    assert result.issues == []


def test_lowercase_key_produces_warning():
    read = _make_read({"myapp": {"dev": {"database_url": "postgres://localhost"}}})
    result = lint_env("myapp", "dev", read)
    keys_with_issues = [i.key for i in result.issues]
    assert "database_url" in keys_with_issues
    severities = [i.severity for i in result.issues if i.key == "database_url"]
    assert "warning" in severities


def test_key_with_space_is_error():
    read = _make_read({"myapp": {"dev": {"BAD KEY": "value"}}})
    result = lint_env("myapp", "dev", read)
    errors = result.errors
    assert any(i.key == "BAD KEY" for i in errors)


def test_empty_value_produces_warning():
    read = _make_read({"myapp": {"staging": {"SECRET": ""}}})
    result = lint_env("myapp", "staging", read)
    warnings = result.warnings
    assert any(i.key == "SECRET" for i in warnings)


def test_value_with_leading_whitespace_produces_warning():
    read = _make_read({"myapp": {"dev": {"API_KEY": "  abc123"}}})
    result = lint_env("myapp", "dev", read)
    assert any(i.key == "API_KEY" and i.severity == "warning" for i in result.issues)


def test_value_with_newline_is_error():
    read = _make_read({"myapp": {"dev": {"MULTILINE": "line1\nline2"}}})
    result = lint_env("myapp", "dev", read)
    assert any(i.key == "MULTILINE" and i.severity == "error" for i in result.issues)
    assert not result.passed


def test_multiple_issues_on_same_key():
    # lowercase key AND empty value
    read = _make_read({"myapp": {"dev": {"bad_key": ""}}})
    result = lint_env("myapp", "dev", read)
    issues_for_key = [i for i in result.issues if i.key == "bad_key"]
    assert len(issues_for_key) >= 2


def test_lint_result_to_dict():
    read = _make_read({"myapp": {"prod": {"GOOD_KEY": "value"}}})
    result = lint_env("myapp", "prod", read)
    d = result.to_dict()
    assert d["project"] == "myapp"
    assert d["environment"] == "prod"
    assert d["passed"] is True
    assert isinstance(d["issues"], list)


def test_lint_issue_to_dict():
    issue = LintIssue(key="FOO", message="Some problem", severity="error")
    d = issue.to_dict()
    assert d == {"key": "FOO", "message": "Some problem", "severity": "error"}


def test_passed_is_false_when_errors_present():
    read = _make_read({"myapp": {"dev": {"MULTILINE": "a\nb"}}})
    result = lint_env("myapp", "dev", read)
    assert not result.passed


def test_empty_env_returns_no_issues():
    read = _make_read({"myapp": {"dev": {}}})
    result = lint_env("myapp", "dev", read)
    assert result.issues == []
    assert result.passed
