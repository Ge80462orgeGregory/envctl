"""Tests for envctl.migrate."""

import pytest
from envctl.migrate import migrate_env, MigrateError


def _make_read(store: dict):
    def _read(project, env):
        return dict(store.get((project, env), {}))
    return _read


_written = {}


def _write(project, env, data):
    _written[(project, env)] = dict(data)


def setup_function():
    _written.clear()


def test_migrate_all_keys_to_empty_target():
    store = {("app", "staging"): {"DB_HOST": "localhost", "PORT": "5432"}}
    result = migrate_env("app", "staging", "app", "production", _make_read(store), _write)
    assert result.total_migrated == 2
    assert _written[("app", "production")] == {"DB_HOST": "localhost", "PORT": "5432"}


def test_migrate_skips_existing_without_overwrite():
    store = {
        ("app", "staging"): {"DB_HOST": "localhost", "PORT": "5432"},
        ("app", "production"): {"DB_HOST": "prod-db"},
    }
    result = migrate_env("app", "staging", "app", "production", _make_read(store), _write)
    assert "DB_HOST" in result.skipped
    assert "PORT" in result.migrated
    assert result.total_skipped == 1


def test_migrate_overwrites_with_flag():
    store = {
        ("app", "staging"): {"DB_HOST": "localhost"},
        ("app", "production"): {"DB_HOST": "prod-db"},
    }
    result = migrate_env(
        "app", "staging", "app", "production", _make_read(store), _write, overwrite=True
    )
    assert result.total_migrated == 1
    assert _written[("app", "production")]["DB_HOST"] == "localhost"


def test_migrate_specific_keys_only():
    store = {("app", "staging"): {"DB_HOST": "localhost", "PORT": "5432", "SECRET": "abc"}}
    result = migrate_env(
        "app", "staging", "app", "production",
        _make_read(store), _write,
        keys=["DB_HOST", "PORT"],
    )
    assert set(result.migrated.keys()) == {"DB_HOST", "PORT"}
    assert "SECRET" not in _written.get(("app", "production"), {})


def test_migrate_with_key_remapping():
    store = {("app", "staging"): {"DB_HOST": "localhost"}}
    result = migrate_env(
        "app", "staging", "app", "production",
        _make_read(store), _write,
        key_map={"DB_HOST": "DATABASE_HOST"},
    )
    assert "DATABASE_HOST" in result.migrated
    assert "DB_HOST" in result.remapped
    assert result.remapped["DB_HOST"] == "DATABASE_HOST"
    assert _written[("app", "production")]["DATABASE_HOST"] == "localhost"


def test_migrate_raises_on_empty_source():
    store = {}
    with pytest.raises(MigrateError, match="empty or does not exist"):
        migrate_env("app", "staging", "app", "production", _make_read(store), _write)


def test_migrate_preserves_existing_target_keys():
    store = {
        ("app", "staging"): {"NEW_KEY": "value"},
        ("app", "production"): {"EXISTING": "keep"},
    }
    migrate_env("app", "staging", "app", "production", _make_read(store), _write)
    assert _written[("app", "production")]["EXISTING"] == "keep"
    assert _written[("app", "production")]["NEW_KEY"] == "value"


def test_migrate_result_to_dict():
    store = {("app", "staging"): {"X": "1"}}
    result = migrate_env("app", "staging", "svc", "prod", _make_read(store), _write)
    d = result.to_dict()
    assert d["source_project"] == "app"
    assert d["target_env"] == "prod"
    assert d["total_migrated"] == 1
