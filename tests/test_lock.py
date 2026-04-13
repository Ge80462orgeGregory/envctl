"""Tests for envctl/lock.py"""

import pytest
from envctl.lock import lock_keys, unlock_keys, get_locked_keys, LockError, LOCK_KEY


def _make_read(data: dict):
    def _read(project, environment):
        return dict(data.get((project, environment), {}))
    return _read


_written = {}


def _write(project, environment, env):
    _written[(project, environment)] = dict(env)


def _read_written(project, environment):
    return dict(_written.get((project, environment), {}))


@pytest.fixture(autouse=True)
def clear_written():
    _written.clear()


def test_lock_keys_sets_lock_key():
    store = {("myapp", "staging"): {"DB_URL": "postgres://localhost", "SECRET": "abc"}}
    read = _make_read(store)
    result = lock_keys("myapp", "staging", ["DB_URL"], read_fn=read, write_fn=_write)
    assert result.locked == ["DB_URL"]
    assert result.already_locked == []
    saved = _read_written("myapp", "staging")
    assert LOCK_KEY in saved
    assert "DB_URL" in saved[LOCK_KEY]


def test_lock_multiple_keys():
    store = {("myapp", "prod"): {"A": "1", "B": "2", "C": "3"}}
    read = _make_read(store)
    result = lock_keys("myapp", "prod", ["A", "B"], read_fn=read, write_fn=_write)
    assert sorted(result.locked) == ["A", "B"]
    saved = _read_written("myapp", "prod")
    assert "A" in saved[LOCK_KEY]
    assert "B" in saved[LOCK_KEY]


def test_lock_already_locked_key():
    store = {("myapp", "staging"): {"DB_URL": "x", LOCK_KEY: "DB_URL"}}
    read = _make_read(store)
    result = lock_keys("myapp", "staging", ["DB_URL"], read_fn=read, write_fn=_write)
    assert result.already_locked == ["DB_URL"]
    assert result.locked == []


def test_lock_raises_for_missing_key():
    store = {("myapp", "staging"): {"EXISTING": "val"}}
    read = _make_read(store)
    with pytest.raises(LockError, match="MISSING_KEY"):
        lock_keys("myapp", "staging", ["MISSING_KEY"], read_fn=read, write_fn=_write)


def test_unlock_keys_removes_from_lock_key():
    store = {("myapp", "prod"): {"A": "1", "B": "2", LOCK_KEY: "A,B"}}
    read = _make_read(store)
    result = unlock_keys("myapp", "prod", ["A"], read_fn=read, write_fn=_write)
    assert result.unlocked == ["A"]
    saved = _read_written("myapp", "prod")
    assert "A" not in saved.get(LOCK_KEY, "")
    assert "B" in saved[LOCK_KEY]


def test_unlock_all_keys_removes_lock_key_entirely():
    store = {("myapp", "prod"): {"A": "1", LOCK_KEY: "A"}}
    read = _make_read(store)
    unlock_keys("myapp", "prod", ["A"], read_fn=read, write_fn=_write)
    saved = _read_written("myapp", "prod")
    assert LOCK_KEY not in saved


def test_unlock_already_unlocked_key():
    store = {("myapp", "staging"): {"X": "1"}}
    read = _make_read(store)
    result = unlock_keys("myapp", "staging", ["X"], read_fn=read, write_fn=_write)
    assert result.already_unlocked == ["X"]
    assert result.unlocked == []


def test_get_locked_keys_returns_list():
    store = {("myapp", "prod"): {"A": "1", "B": "2", LOCK_KEY: "A,B"}}
    read = _make_read(store)
    keys = get_locked_keys("myapp", "prod", read_fn=read)
    assert sorted(keys) == ["A", "B"]


def test_get_locked_keys_empty_when_none():
    store = {("myapp", "local"): {"FOO": "bar"}}
    read = _make_read(store)
    keys = get_locked_keys("myapp", "local", read_fn=read)
    assert keys == []
