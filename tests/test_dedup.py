"""Tests for envctl.dedup."""

import pytest
from envctl.dedup import DedupError, DedupResult, find_duplicates


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_read(store: dict):
    def _read(project: str, env: str):
        return store.get(project, {}).get(env, {})
    return _read


def _make_list(envs_map: dict):
    def _list(project: str):
        return envs_map.get(project, [])
    return _list


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------

def test_duplicate_key_appears_in_multiple_envs():
    store = {
        "myapp": {
            "local": {"DB_URL": "localhost", "SECRET": "abc"},
            "staging": {"DB_URL": "staging-host", "PORT": "8080"},
        }
    }
    result = find_duplicates(
        "myapp",
        _make_list({"myapp": ["local", "staging"]}),
        _make_read(store),
    )
    assert "DB_URL" in result.duplicates
    assert set(result.duplicates["DB_URL"]) == {"local", "staging"}
    assert result.total_duplicate_keys == 1


def test_no_duplicates_when_all_keys_unique():
    store = {
        "myapp": {
            "local": {"A": "1"},
            "prod": {"B": "2"},
        }
    }
    result = find_duplicates(
        "myapp",
        _make_list({"myapp": ["local", "prod"]}),
        _make_read(store),
    )
    assert result.duplicates == {}
    assert result.total_duplicate_keys == 0


def test_key_shared_across_three_envs():
    store = {
        "svc": {
            "local": {"SHARED": "x"},
            "staging": {"SHARED": "y"},
            "prod": {"SHARED": "z"},
        }
    }
    result = find_duplicates(
        "svc",
        _make_list({"svc": ["local", "staging", "prod"]}),
        _make_read(store),
    )
    assert set(result.duplicates["SHARED"]) == {"local", "staging", "prod"}
    assert result.total_duplicate_keys == 1


def test_empty_environments_raises():
    with pytest.raises(DedupError, match="No environments found"):
        find_duplicates(
            "ghost",
            _make_list({}),
            _make_read({}),
        )


def test_to_dict_structure():
    store = {
        "app": {
            "dev": {"KEY": "1"},
            "prod": {"KEY": "2"},
        }
    }
    result = find_duplicates(
        "app",
        _make_list({"app": ["dev", "prod"]}),
        _make_read(store),
    )
    d = result.to_dict()
    assert d["project"] == "app"
    assert "KEY" in d["duplicates"]
    assert d["total_duplicate_keys"] == 1
