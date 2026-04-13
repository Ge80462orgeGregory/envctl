"""Unit tests for envctl.validate."""
import pytest

from envctl.validate import ValidationIssue, ValidationResult, ValidateError, validate_env


def test_valid_env_returns_no_issues():
    result = validate_env("myapp", "prod", {"DATABASE_URL": "postgres://localhost/db", "PORT": "5432"})
    assert result.valid is True
    assert result.issues == []


def test_empty_value_produces_warning():
    result = validate_env("myapp", "staging", {"API_KEY": ""})
    assert result.valid is True  # warning, not error
    assert len(result.warnings) == 1
    assert result.warnings[0].key == "API_KEY"
    assert result.warnings[0].severity == "warning"


def test_key_starting_with_digit_is_error():
    result = validate_env("myapp", "local", {"1BAD_KEY": "value"})
    assert result.valid is False
    assert any(i.key == "1BAD_KEY" and i.severity == "error" for i in result.issues)


def test_key_with_space_is_error():
    result = validate_env("myapp", "local", {"BAD KEY": "value"})
    assert result.valid is False
    assert len(result.errors) == 1


def test_empty_key_is_error():
    result = validate_env("myapp", "local", {"": "value"})
    assert result.valid is False


def test_required_key_missing_is_error():
    result = validate_env("myapp", "prod", {"PORT": "8080"}, required_keys=["DATABASE_URL", "PORT"])
    assert result.valid is False
    missing = [i for i in result.errors if i.key == "DATABASE_URL"]
    assert len(missing) == 1


def test_required_key_present_no_issue():
    result = validate_env("myapp", "prod", {"DATABASE_URL": "postgres://x"}, required_keys=["DATABASE_URL"])
    assert result.valid is True


def test_underscore_prefix_key_is_valid():
    result = validate_env("myapp", "local", {"_PRIVATE": "secret"})
    assert result.valid is True


def test_validation_result_properties():
    result = ValidationResult(
        project="p",
        environment="e",
        issues=[
            ValidationIssue(key="A", message="bad", severity="error"),
            ValidationIssue(key="B", message="meh", severity="warning"),
        ],
    )
    assert not result.valid
    assert len(result.errors) == 1
    assert len(result.warnings) == 1


def test_multiple_issues_accumulate():
    result = validate_env("proj", "env", {"1BAD": "", "GOOD": ""}, required_keys=["MISSING"])
    severities = [i.severity for i in result.issues]
    assert severities.count("error") >= 2  # 1BAD key + MISSING required
    assert "warning" in severities  # empty GOOD
