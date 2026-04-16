"""Tests for envctl.split."""

import pytest
from envctl.split import SplitError, SplitResult, split_env


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_read(data: dict):
    def _read(project, env):
        return dict(data.get((project, env), {}))
    return _read


_written = {}


def _write(project, env, variables):
    _written[(project, env)] = dict(variables)


def _read_written(project, env):
    return _written.get((project, env), {})


def setup_function():
    _written.clear()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_split_by_prefix():
    source = {"DB_HOST": "localhost", "DB_PORT": "5432", "APP_NAME": "myapp", "APP_ENV": "prod"}
    read = _make_read({("proj", "base"): source})

    result = split_env("proj", "base", "db", "app", prefixes_a=["DB_"], read_fn=read, write_fn=_write)

    assert result.keys_to_a == {"DB_HOST": "localhost", "DB_PORT": "5432"}
    assert result.keys_to_b == {"APP_NAME": "myapp", "APP_ENV": "prod"}
    assert result.total_to_a == 2
    assert result.total_to_b == 2


def test_split_by_explicit_keys():
    source = {"FOO": "1", "BAR": "2", "BAZ": "3"}
    read = _make_read({("proj", "base"): source})

    result = split_env("proj", "base", "left", "right", keys_a=["FOO", "BAZ"], read_fn=read, write_fn=_write)

    assert result.keys_to_a == {"FOO": "1", "BAZ": "3"}
    assert result.keys_to_b == {"BAR": "2"}


def test_split_writes_correct_targets():
    source = {"X": "1", "Y": "2"}
    read = _make_read({("proj", "src"): source})

    split_env("proj", "src", "t1", "t2", keys_a=["X"], read_fn=read, write_fn=_write)

    assert _read_written("proj", "t1") == {"X": "1"}
    assert _read_written("proj", "t2") == {"Y": "2"}


def test_split_all_keys_to_a_leaves_b_empty():
    source = {"A": "1", "B": "2"}
    read = _make_read({("proj", "src"): source})

    result = split_env("proj", "src", "full", "empty", keys_a=["A", "B"], read_fn=read, write_fn=_write)

    assert result.total_to_b == 0
    assert _read_written("proj", "empty") == {}


def test_split_raises_when_no_criteria():
    read = _make_read({("proj", "src"): {"K": "v"}})

    with pytest.raises(SplitError, match="At least one"):
        split_env("proj", "src", "a", "b", read_fn=read, write_fn=_write)


def test_split_raises_when_targets_identical():
    read = _make_read({("proj", "src"): {"K": "v"}})

    with pytest.raises(SplitError, match="different"):
        split_env("proj", "src", "same", "same", keys_a=["K"], read_fn=read, write_fn=_write)


def test_split_raises_on_empty_source():
    read = _make_read({})

    with pytest.raises(SplitError, match="empty or does not exist"):
        split_env("proj", "missing", "a", "b", keys_a=["K"], read_fn=read, write_fn=_write)


def test_split_result_to_dict():
    source = {"P_X": "1", "Q_Y": "2"}
    read = _make_read({("proj", "src"): source})

    result = split_env("proj", "src", "p_env", "q_env", prefixes_a=["P_"], read_fn=read, write_fn=_write)
    d = result.to_dict()

    assert d["project"] == "proj"
    assert d["source_env"] == "src"
    assert d["target_a"] == "p_env"
    assert d["target_b"] == "q_env"
    assert d["total_to_a"] == 1
    assert d["total_to_b"] == 1
