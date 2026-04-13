"""Tests for envctl.protect module."""

from __future__ import annotations

from typing import Dict

import pytest

from envctl.protect import (
    ProtectError,
    ProtectResult,
    _PROTECTED_META_KEY,
    _load_protected,
    _save_protected,
    is_protected,
    protect_keys,
    unprotect_keys,
)


_store: Dict[str, Dict[str, str]] = {}


def _make_read(initial: Dict[str, str]):
    _store.clear()
    _store["data"] = dict(initial)

    def _read(project, environment):
        return dict(_store["data"])

    return _read


def _write(project, environment, data):
    _store["data"] = dict(data)


def _read_written():
    return dict(_store["data"])


# --- _load_protected / _save_protected ---

def test_load_protected_empty_env():
    assert _load_protected({}) == []


def test_load_protected_returns_keys():
    env = {_PROTECTED_META_KEY: "FOO,BAR"}
    assert sorted(_load_protected(env)) == ["BAR", "FOO"]


def test_save_protected_adds_sentinel():
    env = {"FOO": "1"}
    updated = _save_protected(env, ["FOO"])
    assert _PROTECTED_META_KEY in updated
    assert "FOO" in updated[_PROTECTED_META_KEY]


def test_save_protected_removes_sentinel_when_empty():
    env = {"FOO": "1", _PROTECTED_META_KEY: "FOO"}
    updated = _save_protected(env, [])
    assert _PROTECTED_META_KEY not in updated


# --- is_protected ---

def test_is_protected_true():
    env = {_PROTECTED_META_KEY: "SECRET_KEY"}
    assert is_protected("SECRET_KEY", env) is True


def test_is_protected_false():
    env = {_PROTECTED_META_KEY: "OTHER"}
    assert is_protected("SECRET_KEY", env) is False


# --- protect_keys ---

def test_protect_keys_marks_existing_key():
    _read = _make_read({"DB_PASS": "hunter2"})
    result = protect_keys("myapp", "prod", ["DB_PASS"], _read, _write)
    assert "DB_PASS" in result.newly_protected
    assert is_protected("DB_PASS", _read_written())


def test_protect_keys_missing_key_goes_to_not_found():
    _read = _make_read({"FOO": "bar"})
    result = protect_keys("myapp", "prod", ["MISSING"], _read, _write)
    assert "MISSING" in result.not_found
    assert result.newly_protected == []


def test_protect_keys_already_protected():
    _read = _make_read({"FOO": "bar", _PROTECTED_META_KEY: "FOO"})
    result = protect_keys("myapp", "prod", ["FOO"], _read, _write)
    assert "FOO" in result.already_protected
    assert result.newly_protected == []


def test_protect_keys_raises_on_empty_project():
    _read = _make_read({})
    with pytest.raises(ProtectError):
        protect_keys("", "prod", ["FOO"], _read, _write)


def test_protect_keys_raises_on_empty_keys():
    _read = _make_read({"FOO": "1"})
    with pytest.raises(ProtectError):
        protect_keys("myapp", "prod", [], _read, _write)


# --- unprotect_keys ---

def test_unprotect_removes_key():
    _read = _make_read({"DB_PASS": "s3cr3t", _PROTECTED_META_KEY: "DB_PASS"})
    result = unprotect_keys("myapp", "prod", ["DB_PASS"], _read, _write)
    assert "DB_PASS" in result.newly_unprotected
    assert not is_protected("DB_PASS", _read_written())


def test_unprotect_not_protected_goes_to_not_found():
    _read = _make_read({"FOO": "bar"})
    result = unprotect_keys("myapp", "prod", ["FOO"], _read, _write)
    assert "FOO" in result.not_found
    assert result.newly_unprotected == []


def test_unprotect_raises_on_empty_keys():
    _read = _make_read({"FOO": "1"})
    with pytest.raises(ProtectError):
        unprotect_keys("myapp", "prod", [], _read, _write)
