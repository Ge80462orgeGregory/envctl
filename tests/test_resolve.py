"""Tests for envctl.resolve."""
from __future__ import annotations

import pytest

from envctl.resolve import resolve_env, ResolveError, ResolveResult


def _make_read(store: dict[str, dict[str, str]]):
    def _read(project: str, environment: str) -> dict[str, str]:
        return store.get(f"{project}/{environment}", {})
    return _read


DEFAULT_PROJECT = "myapp"


def test_resolve_no_references():
    read = _make_read({"myapp/prod": {"KEY": "plain_value"}})
    result = resolve_env(DEFAULT_PROJECT, "prod", read)
    assert result.resolved == {"KEY": "plain_value"}
    assert result.total_substitutions == 0
    assert result.total_unresolved == 0


def test_resolve_single_reference():
    store = {
        "myapp/staging": {"DB_URL": "postgres://staging"},
        "myapp/prod": {"DATABASE_URL": "${staging:DB_URL}"},
    }
    read = _make_read(store)
    result = resolve_env(DEFAULT_PROJECT, "prod", read)
    assert result.resolved["DATABASE_URL"] == "postgres://staging"
    assert result.total_substitutions == 1
    assert result.substitutions[0] == ("DATABASE_URL", "${staging:DB_URL}", "postgres://staging")


def test_resolve_multiple_references_in_one_value():
    store = {
        "myapp/base": {"HOST": "localhost", "PORT": "5432"},
        "myapp/prod": {"DSN": "${base:HOST}:${base:PORT}/mydb"},
    }
    read = _make_read(store)
    result = resolve_env(DEFAULT_PROJECT, "prod", read)
    assert result.resolved["DSN"] == "localhost:5432/mydb"
    assert result.total_substitutions == 2


def test_resolve_unresolved_reference_non_strict():
    store = {
        "myapp/prod": {"KEY": "${staging:MISSING_KEY}"},
    }
    read = _make_read(store)
    result = resolve_env(DEFAULT_PROJECT, "prod", read)
    assert result.total_unresolved == 1
    assert result.unresolved[0] == ("KEY", "${staging:MISSING_KEY}")
    # value left unchanged
    assert result.resolved["KEY"] == "${staging:MISSING_KEY}"


def test_resolve_unresolved_reference_strict_raises():
    store = {
        "myapp/prod": {"KEY": "${staging:MISSING_KEY}"},
    }
    read = _make_read(store)
    with pytest.raises(ResolveError, match="MISSING_KEY"):
        resolve_env(DEFAULT_PROJECT, "prod", read, strict=True)


def test_resolve_missing_environment_raises():
    read = _make_read({})
    with pytest.raises(ResolveError, match="not found"):
        resolve_env(DEFAULT_PROJECT, "ghost", read)


def test_resolve_mixed_plain_and_reference_keys():
    store = {
        "myapp/local": {"SECRET": "abc123"},
        "myapp/prod": {
            "PLAIN": "hello",
            "SECRET_REF": "${local:SECRET}",
        },
    }
    read = _make_read(store)
    result = resolve_env(DEFAULT_PROJECT, "prod", read)
    assert result.resolved["PLAIN"] == "hello"
    assert result.resolved["SECRET_REF"] == "abc123"
    assert result.total_substitutions == 1
    assert result.total_unresolved == 0


def test_resolve_result_total_properties():
    result = ResolveResult(
        resolved={},
        substitutions=[("A", "${x:y}", "val")],
        unresolved=[("B", "${x:z}"), ("C", "${x:w}")],
    )
    assert result.total_substitutions == 1
    assert result.total_unresolved == 2
