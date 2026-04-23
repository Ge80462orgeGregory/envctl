"""Tests for envctl.pivot."""

from __future__ import annotations

import pytest

from envctl.pivot import PivotError, PivotResult, pivot_env


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_read(data: dict):
    """Return a read_env callable backed by *data* keyed as (project, env)."""
    def _read(project: str, env: str):
        return data.get((project, env), {})
    return _read


def _make_list(envs: list):
    def _list(project: str):
        return envs
    return _list


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_pivot_returns_pivot_result():
    read = _make_read({
        ("myapp", "local"): {"A": "1"},
        ("myapp", "prod"): {"A": "2"},
    })
    result = pivot_env("myapp", ["local", "prod"], read)
    assert isinstance(result, PivotResult)


def test_pivot_all_keys_present():
    read = _make_read({
        ("myapp", "local"): {"A": "1", "B": "2"},
        ("myapp", "prod"): {"A": "3", "B": "4"},
    })
    result = pivot_env("myapp", ["local", "prod"], read)
    keys = [r.key for r in result.rows]
    assert keys == ["A", "B"]


def test_pivot_keys_sorted_alphabetically():
    read = _make_read({
        ("myapp", "local"): {"Z": "z", "A": "a"},
        ("myapp", "prod"): {"M": "m"},
    })
    result = pivot_env("myapp", ["local", "prod"], read)
    assert [r.key for r in result.rows] == ["A", "M", "Z"]


def test_pivot_missing_key_is_none():
    read = _make_read({
        ("myapp", "local"): {"A": "1"},
        ("myapp", "prod"): {},
    })
    result = pivot_env("myapp", ["local", "prod"], read)
    row = result.rows[0]
    assert row.values["local"] == "1"
    assert row.values["prod"] is None


def test_pivot_total_missing_count():
    read = _make_read({
        ("myapp", "local"): {"A": "1"},
        ("myapp", "prod"): {},
    })
    result = pivot_env("myapp", ["local", "prod"], read)
    assert result.total_missing == 1


def test_pivot_total_keys():
    read = _make_read({
        ("myapp", "local"): {"A": "1", "B": "2"},
        ("myapp", "prod"): {"C": "3"},
    })
    result = pivot_env("myapp", ["local", "prod"], read)
    assert result.total_keys == 3


def test_pivot_uses_list_environments_when_none_given():
    read = _make_read({
        ("myapp", "dev"): {"X": "1"},
        ("myapp", "staging"): {"X": "2"},
    })
    list_envs = _make_list(["dev", "staging"])
    result = pivot_env("myapp", [], read, list_environments=list_envs)
    assert result.environments == ["dev", "staging"]
    assert result.total_keys == 1


def test_pivot_raises_when_no_envs_and_no_lister():
    read = _make_read({})
    with pytest.raises(PivotError, match="No environments specified"):
        pivot_env("myapp", [], read)


def test_pivot_raises_when_list_returns_empty():
    read = _make_read({})
    with pytest.raises(PivotError, match="no environments"):
        pivot_env("myapp", [], read, list_environments=_make_list([]))


def test_pivot_to_dict_structure():
    read = _make_read({
        ("myapp", "local"): {"K": "v"},
    })
    result = pivot_env("myapp", ["local"], read)
    d = result.to_dict()
    assert d["project"] == "myapp"
    assert d["environments"] == ["local"]
    assert d["total_keys"] == 1
    assert d["total_missing"] == 0
    assert d["rows"][0]["key"] == "K"
