"""Tests for envctl.stats module."""

from __future__ import annotations

from typing import Dict, List

import pytest

from envctl.stats import StatsError, compute_stats


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_list(envs: List[str]):
    def _list(project: str) -> List[str]:
        return envs
    return _list


def _make_read(store: Dict[str, Dict[str, str]]):
    def _read(project: str, env: str) -> Dict[str, str]:
        return store.get(f"{project}/{env}", {})
    return _read


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_compute_stats_basic():
    store = {
        "myapp/local": {"DB_URL": "sqlite", "DEBUG": "true"},
        "myapp/prod": {"DB_URL": "postgres", "SECRET": "abc"},
    }
    stats = compute_stats("myapp", _make_list(["local", "prod"]), _make_read(store))
    assert stats.project == "myapp"
    assert len(stats.environments) == 2


def test_total_keys_across_envs():
    store = {
        "app/local": {"A": "1", "B": "2"},
        "app/staging": {"C": "3"},
    }
    stats = compute_stats("app", _make_list(["local", "staging"]), _make_read(store))
    assert stats.total_keys_across_envs == 3


def test_common_keys():
    store = {
        "app/local": {"DB": "x", "PORT": "8080"},
        "app/prod": {"DB": "y", "PORT": "443", "SECRET": "s"},
    }
    stats = compute_stats("app", _make_list(["local", "prod"]), _make_read(store))
    assert stats.common_keys == ["DB", "PORT"]


def test_empty_values_counted():
    store = {
        "app/local": {"KEY1": "", "KEY2": "value", "KEY3": ""},
    }
    stats = compute_stats("app", _make_list(["local"]), _make_read(store))
    assert stats.environments[0].empty_values == 2


def test_no_environments_raises():
    with pytest.raises(StatsError, match="No environments"):
        compute_stats("ghost", _make_list([]), _make_read({}))


def test_to_dict_structure():
    store = {"proj/dev": {"X": "1"}}
    stats = compute_stats("proj", _make_list(["dev"]), _make_read(store))
    d = stats.to_dict()
    assert d["project"] == "proj"
    assert "environments" in d
    assert "common_keys" in d
    assert d["environments"][0]["total_keys"] == 1


def test_common_keys_empty_when_no_overlap():
    store = {
        "app/a": {"ONLY_A": "1"},
        "app/b": {"ONLY_B": "2"},
    }
    stats = compute_stats("app", _make_list(["a", "b"]), _make_read(store))
    assert stats.common_keys == []
