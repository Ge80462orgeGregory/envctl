"""Tests for envctl.strip module."""

import pytest
from envctl.strip import StripError, StripResult, strip_env

_store: dict = {}


def setup_function():
    _store.clear()


def _make_read(data: dict):
    def _read(project: str, environment: str) -> dict:
        return dict(data.get((project, environment), {}))
    return _read


def _write(project: str, environment: str, data: dict) -> None:
    _store[(project, environment)] = dict(data)


def _read_written(project: str, environment: str) -> dict:
    return _store.get((project, environment), {})


def test_strip_removes_leading_whitespace():
    read = _make_read({("proj", "dev"): {"KEY": "  value"}})
    result = strip_env("proj", "dev", read, _write)
    assert "KEY" in result.stripped
    assert _read_written("proj", "dev")["KEY"] == "value"


def test_strip_removes_trailing_whitespace():
    read = _make_read({("proj", "dev"): {"KEY": "value   "}})
    result = strip_env("proj", "dev", read, _write)
    assert "KEY" in result.stripped
    assert _read_written("proj", "dev")["KEY"] == "value"


def test_strip_removes_both_sides():
    read = _make_read({("proj", "dev"): {"KEY": "  value  "}})
    result = strip_env("proj", "dev", read, _write)
    assert "KEY" in result.stripped
    assert _read_written("proj", "dev")["KEY"] == "value"


def test_strip_unchanged_when_no_whitespace():
    read = _make_read({("proj", "dev"): {"KEY": "clean"}})
    result = strip_env("proj", "dev", read, _write)
    assert "KEY" in result.unchanged
    assert result.total_stripped == 0


def test_strip_only_specified_keys():
    read = _make_read({("proj", "dev"): {"A": "  hello", "B": "  world"}})
    result = strip_env("proj", "dev", read, _write, keys=["A"])
    assert "A" in result.stripped
    assert "B" not in result.stripped
    assert _read_written("proj", "dev")["B"] == "  world"


def test_strip_skips_missing_keys_in_keys_list():
    read = _make_read({("proj", "dev"): {"A": "  hello"}})
    result = strip_env("proj", "dev", read, _write, keys=["A", "MISSING"])
    assert "A" in result.stripped
    assert "MISSING" not in result.stripped
    assert "MISSING" not in result.unchanged


def test_strip_total_stripped_count():
    read = _make_read({("proj", "dev"): {"A": " x ", "B": " y ", "C": "z"}})
    result = strip_env("proj", "dev", read, _write)
    assert result.total_stripped == 2


def test_strip_raises_on_empty_env():
    read = _make_read({})
    with pytest.raises(StripError, match="empty or does not exist"):
        strip_env("proj", "dev", read, _write)


def test_strip_raises_on_read_error():
    def bad_read(p, e):
        raise RuntimeError("disk failure")
    with pytest.raises(StripError, match="Failed to read"):
        strip_env("proj", "dev", bad_read, _write)


def test_strip_raises_on_write_error():
    read = _make_read({("proj", "dev"): {"KEY": " val "}})
    def bad_write(p, e, d):
        raise RuntimeError("write failure")
    with pytest.raises(StripError, match="Failed to write"):
        strip_env("proj", "dev", read, bad_write)


def test_strip_result_to_dict():
    read = _make_read({("proj", "dev"): {"A": " x "}})
    result = strip_env("proj", "dev", read, _write)
    d = result.to_dict()
    assert d["project"] == "proj"
    assert d["environment"] == "dev"
    assert "A" in d["stripped"]
    assert d["total_stripped"] == 1
