"""Tests for envctl.pin module."""

from __future__ import annotations

import pytest

from envctl.pin import (
    PinError,
    PinResult,
    get_pinned_keys,
    is_pinned,
    pin_keys,
    unpin_keys,
)

_STORE: dict[tuple[str, str], dict[str, str]] = {}


def _make_read(initial: dict[str, str] | None = None):
    _STORE.clear()
    if initial:
        _STORE[("proj", "dev")] = dict(initial)
    else:
        _STORE[("proj", "dev")] = {}

    def _read(project: str, environment: str) -> dict[str, str]:
        return dict(_STORE.get((project, environment), {}))

    return _read


def _write(project: str, environment: str, data: dict[str, str]) -> None:
    _STORE[(project, environment)] = dict(data)


def _read_written() -> dict[str, str]:
    return dict(_STORE.get(("proj", "dev"), {}))


# --- pin_keys ---

def test_pin_keys_marks_existing_key():
    read = _make_read({"DB_URL": "postgres://localhost"})
    result = pin_keys("proj", "dev", ["DB_URL"], read, _write)
    assert "DB_URL" in result.pinned
    assert result.already_pinned == []
    assert "__pinned__" in _read_written()
    assert "DB_URL" in _read_written()["__pinned__"]


def test_pin_keys_already_pinned_key():
    read = _make_read({"DB_URL": "postgres://localhost", "__pinned__": "DB_URL"})
    result = pin_keys("proj", "dev", ["DB_URL"], read, _write)
    assert result.already_pinned == ["DB_URL"]
    assert result.pinned == []


def test_pin_keys_raises_for_missing_key():
    read = _make_read({"DB_URL": "postgres://localhost"})
    with pytest.raises(PinError, match="MISSING_KEY"):
        pin_keys("proj", "dev", ["MISSING_KEY"], read, _write)


def test_pin_multiple_keys():
    read = _make_read({"A": "1", "B": "2", "C": "3"})
    result = pin_keys("proj", "dev", ["A", "B"], read, _write)
    assert set(result.pinned) == {"A", "B"}
    pinned_raw = _read_written()["__pinned__"]
    assert "A" in pinned_raw
    assert "B" in pinned_raw


# --- unpin_keys ---

def test_unpin_removes_key():
    read = _make_read({"DB_URL": "postgres://localhost", "__pinned__": "DB_URL"})
    result = unpin_keys("proj", "dev", ["DB_URL"], read, _write)
    assert result.unpinned == ["DB_URL"]
    assert result.not_pinned == []
    data = _read_written()
    assert "__pinned__" not in data or "DB_URL" not in data.get("__pinned__", "")


def test_unpin_key_not_pinned():
    read = _make_read({"DB_URL": "postgres://localhost"})
    result = unpin_keys("proj", "dev", ["DB_URL"], read, _write)
    assert result.not_pinned == ["DB_URL"]
    assert result.unpinned == []


def test_unpin_all_clears_pins_key():
    read = _make_read({"A": "1", "__pinned__": "A"})
    unpin_keys("proj", "dev", ["A"], read, _write)
    assert "__pinned__" not in _read_written()


# --- get_pinned_keys / is_pinned ---

def test_get_pinned_keys_returns_list():
    read = _make_read({"A": "1", "B": "2", "__pinned__": "A,B"})
    pins = get_pinned_keys("proj", "dev", read)
    assert set(pins) == {"A", "B"}


def test_get_pinned_keys_empty_when_none():
    read = _make_read({"A": "1"})
    pins = get_pinned_keys("proj", "dev", read)
    assert pins == []


def test_is_pinned_true():
    read = _make_read({"SECRET": "abc", "__pinned__": "SECRET"})
    assert is_pinned("SECRET", "proj", "dev", read) is True


def test_is_pinned_false():
    read = _make_read({"SECRET": "abc"})
    assert is_pinned("SECRET", "proj", "dev", read) is False
