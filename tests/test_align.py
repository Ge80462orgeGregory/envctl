"""Tests for envctl.align."""

import pytest
from envctl.align import align_env, AlignError

_store: dict = {}


def _make_read(data: dict):
    def _read(project, environment):
        return dict(data.get((project, environment), {}))
    return _read


def _write(project, environment, variables):
    _store[(project, environment)] = dict(variables)


def _read_written(project, environment):
    return _store.get((project, environment), {})


def setup_function():
    _store.clear()


def test_align_pads_short_values():
    data = {("proj", "dev"): {"A": "hi", "B": "hello"}}
    result = align_env("proj", "dev", width=8, read_env=_make_read(data), write_env=_write)
    assert result.aligned["A"] == "hi      "
    assert result.aligned["B"] == "hello   "
    assert result.total_changed == 2


def test_align_does_not_change_exact_width_values():
    data = {("proj", "dev"): {"KEY": "12345678"}}
    result = align_env("proj", "dev", width=8, read_env=_make_read(data), write_env=_write)
    assert result.aligned["KEY"] == "12345678"
    assert result.total_changed == 0


def test_align_truncates_long_values_when_flag_set():
    data = {("proj", "dev"): {"K": "abcdefghij"}}
    result = align_env("proj", "dev", width=5, truncate=True, read_env=_make_read(data), write_env=_write)
    assert result.aligned["K"] == "abcde"
    assert result.total_changed == 1


def test_align_does_not_truncate_by_default():
    data = {("proj", "dev"): {"K": "abcdefghij"}}
    result = align_env("proj", "dev", width=5, read_env=_make_read(data), write_env=_write)
    assert result.aligned["K"] == "abcdefghij"  # unchanged
    assert result.total_changed == 0


def test_align_custom_fill_char():
    data = {("proj", "dev"): {"X": "abc"}}
    result = align_env("proj", "dev", width=6, fill_char="0", read_env=_make_read(data), write_env=_write)
    assert result.aligned["X"] == "abc000"


def test_align_raises_on_invalid_width():
    data = {("proj", "dev"): {"K": "val"}}
    with pytest.raises(AlignError, match="width must be"):
        align_env("proj", "dev", width=0, read_env=_make_read(data), write_env=_write)


def test_align_raises_on_invalid_fill_char():
    data = {("proj", "dev"): {"K": "val"}}
    with pytest.raises(AlignError, match="fill_char"):
        align_env("proj", "dev", width=5, fill_char="ab", read_env=_make_read(data), write_env=_write)


def test_align_raises_when_env_missing():
    with pytest.raises(AlignError, match="No environment"):
        align_env("proj", "missing", width=5, read_env=_make_read({}), write_env=_write)


def test_align_writes_result_to_store():
    data = {("proj", "dev"): {"A": "x", "B": "yy"}}
    align_env("proj", "dev", width=4, read_env=_make_read(data), write_env=_write)
    written = _read_written("proj", "dev")
    assert written["A"] == "x   "
    assert written["B"] == "yy  "


def test_align_result_metadata():
    data = {("proj", "prod"): {"Z": "val"}}
    result = align_env("proj", "prod", width=6, read_env=_make_read(data), write_env=_write)
    assert result.project == "proj"
    assert result.environment == "prod"
    assert "Z" in result.original
