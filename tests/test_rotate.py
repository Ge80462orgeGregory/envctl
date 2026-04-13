"""Tests for envctl.rotate."""

from __future__ import annotations

import pytest

from envctl.rotate import RotateError, RotateResult, rotate_env


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_read(data: dict):
    def _read(project, environment):
        return dict(data.get((project, environment), {}))
    return _read


_written: dict = {}


def _write(project, environment, vars_):
    _written[(project, environment)] = dict(vars_)


def _upper_transform(key: str, value: str) -> str:
    return value.upper()


def _noop_transform(key: str, value: str) -> str:
    return value


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_rotate_all_keys():
    _written.clear()
    read = _make_read({("myapp", "staging"): {"FOO": "bar", "BAZ": "qux"}})
    result = rotate_env("myapp", "staging", None, _upper_transform, _read=read, _write=_write)
    assert set(result.rotated) == {"FOO", "BAZ"}
    assert result.skipped == []
    assert _written[("myapp", "staging")] == {"FOO": "BAR", "BAZ": "QUX"}


def test_rotate_specific_keys():
    _written.clear()
    read = _make_read({("myapp", "staging"): {"FOO": "bar", "BAZ": "qux"}})
    result = rotate_env("myapp", "staging", ["FOO"], _upper_transform, _read=read, _write=_write)
    assert result.rotated == ["FOO"]
    assert result.skipped == []
    assert _written[("myapp", "staging")]["FOO"] == "BAR"
    assert _written[("myapp", "staging")]["BAZ"] == "qux"


def test_rotate_skips_unchanged_keys():
    _written.clear()
    read = _make_read({("myapp", "prod"): {"KEY": "VALUE"}})
    result = rotate_env("myapp", "prod", None, _noop_transform, _read=read, _write=_write)
    assert result.rotated == []
    assert result.skipped == ["KEY"]
    assert ("myapp", "prod") not in _written


def test_rotate_dry_run_does_not_write():
    _written.clear()
    read = _make_read({("myapp", "local"): {"SECRET": "old"}})
    result = rotate_env(
        "myapp", "local", None, _upper_transform, dry_run=True, _read=read, _write=_write
    )
    assert result.rotated == ["SECRET"]
    assert ("myapp", "local") not in _written


def test_rotate_raises_on_missing_key():
    read = _make_read({("myapp", "staging"): {"FOO": "bar"}})
    with pytest.raises(RotateError, match="MISSING"):
        rotate_env("myapp", "staging", ["MISSING"], _upper_transform, _read=read, _write=_write)


def test_rotate_raises_on_empty_environment():
    read = _make_read({})
    with pytest.raises(RotateError, match="empty or does not exist"):
        rotate_env("myapp", "ghost", None, _upper_transform, _read=read, _write=_write)


def test_rotate_result_total_rotated():
    result = RotateResult(project="p", environment="e", rotated=["A", "B"], skipped=["C"])
    assert result.total_rotated == 2
