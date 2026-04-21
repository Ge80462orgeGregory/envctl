"""Tests for envctl.blank — find_blank and fill_blank."""
from __future__ import annotations

import pytest
from envctl.blank import BlankError, BlankResult, fill_blank, find_blank

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

_store: dict = {}


def _make_read(data: dict):
    def _read(project: str, environment: str):
        return dict(data.get((project, environment), {}))
    return _read


def _write(project: str, environment: str, variables: dict):
    _store[(project, environment)] = dict(variables)


def _read_written(project: str, environment: str) -> dict:
    return dict(_store.get((project, environment), {}))


def setup_function():
    _store.clear()


# ---------------------------------------------------------------------------
# find_blank
# ---------------------------------------------------------------------------

def test_find_blank_identifies_empty_values():
    data = {"A": "hello", "B": "", "C": "   ", "D": "world"}
    result = find_blank("proj", "dev", _make_read({("proj", "dev"): data}))
    assert isinstance(result, BlankResult)
    assert set(result.blank_keys) == {"B", "C"}
    assert result.total_blank() == 2


def test_find_blank_no_blank_keys():
    data = {"X": "1", "Y": "2"}
    result = find_blank("proj", "dev", _make_read({("proj", "dev"): data}))
    assert result.blank_keys == []
    assert result.total_blank() == 0


def test_find_blank_all_blank():
    data = {"A": "", "B": " ", "C": "\t"}
    result = find_blank("proj", "dev", _make_read({("proj", "dev"): data}))
    assert result.total_blank() == 3


def test_find_blank_missing_env_raises():
    with pytest.raises(BlankError):
        find_blank("proj", "missing", _make_read({}))


# ---------------------------------------------------------------------------
# fill_blank
# ---------------------------------------------------------------------------

def test_fill_blank_replaces_empty_values():
    data = {"A": "set", "B": "", "C": "  "}
    _store[("proj", "dev")] = dict(data)
    result = fill_blank("proj", "dev", "PLACEHOLDER", _make_read({("proj", "dev"): data}), _write)
    assert set(result.filled_keys) == {"B", "C"}
    written = _read_written("proj", "dev")
    assert written["B"] == "PLACEHOLDER"
    assert written["C"] == "PLACEHOLDER"
    assert written["A"] == "set"


def test_fill_blank_no_blanks_does_not_write():
    data = {"A": "val"}
    result = fill_blank("proj", "dev", "X", _make_read({("proj", "dev"): data}), _write)
    assert result.filled_keys == []
    assert result.total_filled() == 0
    assert _store == {}


def test_fill_blank_specific_keys_only():
    data = {"A": "", "B": "", "C": "ok"}
    _store[("proj", "dev")] = dict(data)
    result = fill_blank("proj", "dev", "FILL", _make_read({("proj", "dev"): data}), _write, keys=["A"])
    assert result.filled_keys == ["A"]
    written = _read_written("proj", "dev")
    assert written["A"] == "FILL"
    assert written["B"] == ""  # untouched


def test_fill_blank_to_dict_shape():
    data = {"K": ""}
    _store[("p", "e")] = dict(data)
    result = fill_blank("p", "e", "V", _make_read({("p", "e"): data}), _write)
    d = result.to_dict()
    assert d["project"] == "p"
    assert d["environment"] == "e"
    assert "blank_keys" in d
    assert "filled_keys" in d
    assert "total_blank" in d
    assert "total_filled" in d


def test_fill_blank_missing_env_raises():
    with pytest.raises(BlankError):
        fill_blank("proj", "ghost", "X", _make_read({}), _write)
