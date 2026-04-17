"""Tests for envctl.lowercase."""
import pytest
from envctl.lowercase import lowercase_env, LowercaseError


def _make_read(data):
    def _read(project, environment):
        return dict(data.get((project, environment), {}))
    return _read


_written = {}


def _write(project, environment, data):
    _written[(project, environment)] = dict(data)


def setup_function():
    _written.clear()


def _read_written(project, environment):
    return _written.get((project, environment), {})


def test_lowercase_converts_values():
    read = _make_read({("proj", "dev"): {"KEY": "HELLO", "OTHER": "WORLD"}})
    result = lowercase_env("proj", "dev", read, _write)
    assert result.total_changed == 2
    assert result.changes["KEY"] == "hello"
    assert result.changes["OTHER"] == "world"
    assert _read_written("proj", "dev")["KEY"] == "hello"


def test_lowercase_skips_already_lowercase():
    read = _make_read({("proj", "dev"): {"KEY": "hello", "OTHER": "WORLD"}})
    result = lowercase_env("proj", "dev", read, _write)
    assert result.total_changed == 1
    assert "KEY" not in result.changes
    assert "OTHER" in result.changes


def test_lowercase_specific_keys_only():
    read = _make_read({("proj", "dev"): {"A": "HELLO", "B": "WORLD"}})
    result = lowercase_env("proj", "dev", read, _write, keys=["A"])
    assert result.total_changed == 1
    assert "A" in result.changes
    assert "B" not in result.changes
    written = _read_written("proj", "dev")
    assert written["B"] == "WORLD"  # unchanged


def test_lowercase_no_changes_does_not_write():
    read = _make_read({("proj", "dev"): {"KEY": "already"}})
    result = lowercase_env("proj", "dev", read, _write)
    assert result.total_changed == 0
    assert _read_written("proj", "dev") == {}


def test_lowercase_missing_env_raises():
    read = _make_read({})
    with pytest.raises(LowercaseError):
        lowercase_env("proj", "missing", read, _write)


def test_lowercase_to_dict():
    read = _make_read({("p", "e"): {"X": "ABC"}})
    result = lowercase_env("p", "e", read, _write)
    d = result.to_dict()
    assert d["project"] == "p"
    assert d["environment"] == "e"
    assert d["total_changed"] == 1
    assert d["changes"]["X"] == "abc"
