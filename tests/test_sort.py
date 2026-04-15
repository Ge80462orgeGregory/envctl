"""Tests for envctl.sort."""
from __future__ import annotations

import pytest
from envctl.sort import SortError, SortResult, sort_env


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_store: dict = {}


def _make_read(data: dict):
    def _read(project, environment):
        return dict(data.get((project, environment), {}))
    return _read


def _read(project, environment):
    return dict(_store.get((project, environment), {}))


def _write(project, environment, data):
    _store[(project, environment)] = dict(data)


def _read_written(project, environment):
    return _store.get((project, environment), {})


def setup_function():
    _store.clear()


# ---------------------------------------------------------------------------
# Tests — alphabetical (default)
# ---------------------------------------------------------------------------

def test_sort_alpha_orders_keys():
    read = _make_read({("proj", "dev"): {"ZEBRA": "1", "APPLE": "2", "MANGO": "3"}})
    result = sort_env("proj", "dev", read_env=read, write_env=_write)
    assert result.sorted_order == ["APPLE", "MANGO", "ZEBRA"]
    assert result.changed is True


def test_sort_alpha_already_sorted_no_write():
    data = {"APPLE": "1", "MANGO": "2", "ZEBRA": "3"}
    read = _make_read({("proj", "dev"): data})
    result = sort_env("proj", "dev", read_env=read, write_env=_write)
    assert result.changed is False
    # write should not have been called
    assert _read_written("proj", "dev") == {}


# ---------------------------------------------------------------------------
# Tests — reverse strategy
# ---------------------------------------------------------------------------

def test_sort_reverse_strategy():
    read = _make_read({("proj", "dev"): {"APPLE": "1", "MANGO": "2", "ZEBRA": "3"}})
    result = sort_env("proj", "dev", strategy="reverse", read_env=read, write_env=_write)
    assert result.sorted_order == ["ZEBRA", "MANGO", "APPLE"]
    assert result.changed is True


# ---------------------------------------------------------------------------
# Tests — length strategy
# ---------------------------------------------------------------------------

def test_sort_by_length_strategy():
    read = _make_read({("proj", "dev"): {"AB": "1", "ABCDE": "2", "ABC": "3"}})
    result = sort_env("proj", "dev", strategy="length", read_env=read, write_env=_write)
    assert result.sorted_order == ["AB", "ABC", "ABCDE"]


# ---------------------------------------------------------------------------
# Tests — errors
# ---------------------------------------------------------------------------

def test_sort_unknown_strategy_raises():
    read = _make_read({("proj", "dev"): {"KEY": "val"}})
    with pytest.raises(SortError, match="Unknown sort strategy"):
        sort_env("proj", "dev", strategy="bogus", read_env=read, write_env=_write)


def test_sort_empty_env_raises():
    read = _make_read({})  # env doesn't exist
    with pytest.raises(SortError, match="empty or does not exist"):
        sort_env("proj", "dev", read_env=read, write_env=_write)


# ---------------------------------------------------------------------------
# Tests — result structure
# ---------------------------------------------------------------------------

def test_sort_result_to_dict():
    read = _make_read({("p", "e"): {"Z": "1", "A": "2"}})
    result = sort_env("p", "e", read_env=read, write_env=_write)
    d = result.to_dict()
    assert d["project"] == "p"
    assert d["environment"] == "e"
    assert d["changed"] is True
    assert "original_order" in d
    assert "sorted_order" in d
