"""Tests for envctl.redact."""

from __future__ import annotations

import pytest

from envctl.redact import (
    DEFAULT_PLACEHOLDER,
    RedactError,
    RedactResult,
    _is_sensitive,
    redact_env,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_store: dict[tuple[str, str], dict[str, str]] = {}


def _make_read(data: dict[str, str]):
    def _read(project: str, environment: str) -> dict[str, str]:
        return dict(data)
    return _read


def _read(project: str, environment: str) -> dict[str, str]:
    return dict(_store.get((project, environment), {}))


def _write(project: str, environment: str, data: dict[str, str]) -> None:
    _store[(project, environment)] = dict(data)


def _read_written(project: str, environment: str) -> dict[str, str]:
    return dict(_store.get((project, environment), {}))


def setup_function():
    _store.clear()


# ---------------------------------------------------------------------------
# Unit tests for _is_sensitive
# ---------------------------------------------------------------------------

def test_sensitive_key_detected():
    from envctl.redact import _DEFAULT_SENSITIVE_PATTERNS
    assert _is_sensitive("DB_PASSWORD", _DEFAULT_SENSITIVE_PATTERNS) is True


def test_non_sensitive_key_not_detected():
    from envctl.redact import _DEFAULT_SENSITIVE_PATTERNS
    assert _is_sensitive("APP_NAME", _DEFAULT_SENSITIVE_PATTERNS) is False


def test_token_key_detected():
    from envctl.redact import _DEFAULT_SENSITIVE_PATTERNS
    assert _is_sensitive("GITHUB_TOKEN", _DEFAULT_SENSITIVE_PATTERNS) is True


# ---------------------------------------------------------------------------
# redact_env tests
# ---------------------------------------------------------------------------

def test_redact_auto_detects_sensitive_keys():
    env = {"DB_PASSWORD": "hunter2", "APP_NAME": "myapp", "API_KEY": "abc123"}
    _store[("proj", "prod")] = dict(env)

    result = redact_env("proj", "prod", read=_read, write=_write)

    written = _read_written("proj", "prod")
    assert written["DB_PASSWORD"] == DEFAULT_PLACEHOLDER
    assert written["API_KEY"] == DEFAULT_PLACEHOLDER
    assert written["APP_NAME"] == "myapp"
    assert result.total_redacted == 2
    assert sorted(result.redacted_keys) == ["API_KEY", "DB_PASSWORD"]


def test_redact_explicit_keys_only():
    env = {"DB_PASSWORD": "secret", "APP_NAME": "myapp", "DEBUG": "true"}
    _store[("proj", "staging")] = dict(env)

    result = redact_env("proj", "staging", keys=["DEBUG"], read=_read, write=_write)

    written = _read_written("proj", "staging")
    assert written["DEBUG"] == DEFAULT_PLACEHOLDER
    assert written["DB_PASSWORD"] == "secret"  # not in explicit keys
    assert result.total_redacted == 1


def test_redact_skips_already_redacted_values():
    env = {"DB_PASSWORD": DEFAULT_PLACEHOLDER, "APP_NAME": "x"}
    _store[("proj", "dev")] = dict(env)

    result = redact_env("proj", "dev", read=_read, write=_write)

    assert result.total_redacted == 0
    assert result.redacted_keys == []


def test_redact_custom_placeholder():
    env = {"SECRET_KEY": "topsecret"}
    _store[("proj", "prod")] = dict(env)

    result = redact_env("proj", "prod", placeholder="***", read=_read, write=_write)

    written = _read_written("proj", "prod")
    assert written["SECRET_KEY"] == "***"
    assert result.total_redacted == 1


def test_redact_raises_on_missing_environment():
    with pytest.raises(RedactError):
        redact_env("proj", "nonexistent", read=_make_read({}), write=_write)


def test_redact_result_fields():
    env = {"AUTH_TOKEN": "xyz"}
    _store[("p", "e")] = dict(env)

    result = redact_env("p", "e", read=_read, write=_write)

    assert isinstance(result, RedactResult)
    assert result.project == "p"
    assert result.environment == "e"
