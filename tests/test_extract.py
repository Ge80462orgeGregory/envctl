"""Tests for envctl.extract."""

import pytest
from envctl.extract import extract_env, ExtractError


def _make_read(store: dict):
    def _read(project, env):
        return dict(store.get((project, env), {}))
    return _read


_written = {}


def _write(project, env, data):
    _written[(project, env)] = dict(data)


def _read_written(project, env):
    return _written.get((project, env), {})


def setup_function():
    _written.clear()


def test_extract_copies_specified_keys():
    read = _make_read({
        ("app", "staging"): {"DB_URL": "postgres://staging", "SECRET": "abc", "PORT": "5432"},
        ("app", "local"): {},
    })
    result = extract_env("app", "staging", "local", ["DB_URL", "PORT"], read, _write)
    assert result.extracted == {"DB_URL": "postgres://staging", "PORT": "5432"}
    assert result.skipped == []
    assert _read_written("app", "local") == {"DB_URL": "postgres://staging", "PORT": "5432"}


def test_extract_skips_missing_keys():
    read = _make_read({
        ("app", "staging"): {"DB_URL": "postgres://staging"},
        ("app", "local"): {},
    })
    result = extract_env("app", "staging", "local", ["DB_URL", "MISSING_KEY"], read, _write)
    assert "DB_URL" in result.extracted
    assert "MISSING_KEY" in result.skipped


def test_extract_skips_existing_keys_without_overwrite():
    read = _make_read({
        ("app", "staging"): {"DB_URL": "new_value"},
        ("app", "local"): {"DB_URL": "old_value"},
    })
    result = extract_env("app", "staging", "local", ["DB_URL"], read, _write)
    assert result.total_extracted == 0
    assert "DB_URL" in result.skipped


def test_extract_overwrites_existing_keys_with_flag():
    read = _make_read({
        ("app", "staging"): {"DB_URL": "new_value"},
        ("app", "local"): {"DB_URL": "old_value"},
    })
    result = extract_env("app", "staging", "local", ["DB_URL"], read, _write, overwrite=True)
    assert result.extracted == {"DB_URL": "new_value"}
    assert _read_written("app", "local")["DB_URL"] == "new_value"


def test_extract_preserves_existing_target_keys():
    read = _make_read({
        ("app", "staging"): {"NEW_KEY": "val"},
        ("app", "local"): {"EXISTING": "kept"},
    })
    extract_env("app", "staging", "local", ["NEW_KEY"], read, _write)
    written = _read_written("app", "local")
    assert written["EXISTING"] == "kept"
    assert written["NEW_KEY"] == "val"


def test_extract_raises_on_empty_keys_list():
    read = _make_read({("app", "staging"): {"A": "1"}})
    with pytest.raises(ExtractError, match="No keys specified"):
        extract_env("app", "staging", "local", [], read, _write)


def test_extract_raises_on_empty_source():
    read = _make_read({})
    with pytest.raises(ExtractError, match="empty or does not exist"):
        extract_env("app", "staging", "local", ["KEY"], read, _write)


def test_extract_result_to_dict():
    read = _make_read({
        ("app", "staging"): {"X": "1"},
        ("app", "prod"): {},
    })
    result = extract_env("app", "staging", "prod", ["X"], read, _write)
    d = result.to_dict()
    assert d["project"] == "app"
    assert d["source_env"] == "staging"
    assert d["target_env"] == "prod"
    assert d["total_extracted"] == 1
