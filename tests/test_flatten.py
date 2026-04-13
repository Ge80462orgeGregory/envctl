"""Tests for envctl.flatten."""

from __future__ import annotations

import pytest

from envctl.flatten import FlattenError, flatten_envs


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_read(store: dict[tuple[str, str], dict[str, str]]):
    def _read(project: str, env: str) -> dict[str, str]:
        return dict(store.get((project, env), {}))
    return _read


def _make_list(available: dict[str, list[str]]):
    def _list(project: str) -> list[str]:
        return list(available.get(project, []))
    return _list


_STORE = {
    ("myapp", "local"): {"DB": "localhost", "PORT": "5432", "DEBUG": "true"},
    ("myapp", "staging"): {"DB": "staging-db", "PORT": "5432", "CACHE": "redis"},
    ("myapp", "prod"): {"DB": "prod-db", "PORT": "5433", "CACHE": "redis"},
}
_AVAILABLE = {"myapp": ["local", "staging", "prod"]}
_read = _make_read(_STORE)
_list = _make_list(_AVAILABLE)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_flatten_merges_unique_keys():
    result = flatten_envs("myapp", ["local", "staging"], _read, _list)
    assert "DEBUG" in result.merged   # only in local
    assert "CACHE" in result.merged   # only in staging


def test_flatten_last_writer_wins_on_conflict():
    result = flatten_envs("myapp", ["local", "staging"], _read, _list)
    # DB conflicts; staging is last -> staging wins
    assert result.merged["DB"] == "staging-db"


def test_flatten_priority_env_wins():
    result = flatten_envs(
        "myapp", ["local", "staging", "prod"], _read, _list, priority="local"
    )
    assert result.merged["DB"] == "localhost"


def test_flatten_skip_conflicts_omits_conflicting_keys():
    result = flatten_envs(
        "myapp", ["local", "staging"], _read, _list, skip_conflicts=True
    )
    assert "DB" not in result.merged
    assert "DEBUG" in result.merged
    assert "CACHE" in result.merged


def test_flatten_reports_conflicts():
    result = flatten_envs("myapp", ["local", "staging", "prod"], _read, _list)
    assert "DB" in result.conflicts
    assert result.total_conflicts >= 1


def test_flatten_no_conflict_for_identical_values():
    # PORT is 5432 in local and staging — same value, no conflict
    result = flatten_envs("myapp", ["local", "staging"], _read, _list)
    assert "PORT" not in result.conflicts
    assert result.merged["PORT"] == "5432"


def test_flatten_raises_for_missing_environment():
    with pytest.raises(FlattenError, match="ghost"):
        flatten_envs("myapp", ["local", "ghost"], _read, _list)


def test_flatten_raises_for_unknown_project():
    with pytest.raises(FlattenError, match="no environments"):
        flatten_envs("unknown", ["local"], _read, _list)


def test_flatten_raises_when_no_environments_given():
    with pytest.raises(FlattenError, match="At least one"):
        flatten_envs("myapp", [], _read, _list)


def test_flatten_result_total_keys():
    result = flatten_envs("myapp", ["local", "staging"], _read, _list)
    assert result.total_keys == len(result.merged)
