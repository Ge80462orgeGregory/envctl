"""Tests for envctl.touch."""

from __future__ import annotations

import pytest

from envctl.touch import TouchError, TouchResult, touch_env

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

_store: dict = {}


def _make_read(data: dict):
    def _read(project: str, environment: str) -> dict:
        return dict(data.get((project, environment), {}))
    return _read


def _write(project: str, environment: str, variables: dict) -> None:
    _store[(project, environment)] = dict(variables)


def _read_written(project: str, environment: str) -> dict:
    return dict(_store.get((project, environment), {}))


def setup_function():
    _store.clear()


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------

def test_touch_adds_missing_key():
    read = _make_read({})
    result = touch_env("proj", "dev", ["NEW_KEY"], default="", read=read, write=_write)
    assert "NEW_KEY" in result.added
    assert result.total_added == 1
    assert _read_written("proj", "dev")["NEW_KEY"] == ""


def test_touch_skips_existing_key():
    read = _make_read({("proj", "dev"): {"EXISTING": "hello"}})
    result = touch_env("proj", "dev", ["EXISTING"], read=read, write=_write)
    assert "EXISTING" in result.skipped
    assert result.total_added == 0
    # write should not have been called — store remains empty
    assert _read_written("proj", "dev") == {}


def test_touch_uses_custom_default():
    read = _make_read({})
    touch_env("proj", "dev", ["PORT"], default="8080", read=read, write=_write)
    assert _read_written("proj", "dev")["PORT"] == "8080"


def test_touch_multiple_keys_mixed():
    read = _make_read({("proj", "dev"): {"A": "1"}})
    result = touch_env("proj", "dev", ["A", "B", "C"], default="x", read=read, write=_write)
    assert result.skipped == ["A"]
    assert set(result.added) == {"B", "C"}
    written = _read_written("proj", "dev")
    assert written["B"] == "x"
    assert written["C"] == "x"
    assert written["A"] == "1"


def test_touch_result_to_dict():
    read = _make_read({})
    result = touch_env("proj", "staging", ["K"], read=read, write=_write)
    d = result.to_dict()
    assert d["project"] == "proj"
    assert d["environment"] == "staging"
    assert "K" in d["added"]
    assert d["total_added"] == 1


def test_touch_raises_on_empty_keys_list():
    read = _make_read({})
    with pytest.raises(TouchError, match="at least one key"):
        touch_env("proj", "dev", [], read=read, write=_write)


def test_touch_raises_on_empty_key_string():
    read = _make_read({})
    with pytest.raises(TouchError, match="must not be empty"):
        touch_env("proj", "dev", [""], read=read, write=_write)


def test_touch_raises_without_read_write():
    with pytest.raises(TouchError):
        touch_env("proj", "dev", ["K"], read=None, write=None)
