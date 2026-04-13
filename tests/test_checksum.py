"""Tests for envctl.checksum."""

from __future__ import annotations

import pytest

from envctl.checksum import (
    ChecksumError,
    ChecksumResult,
    VerifyResult,
    _compute,
    compute_checksum,
    verify_checksum,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_read(store: dict[tuple[str, str], dict[str, str]]):
    def _read(project: str, environment: str) -> dict[str, str]:
        return store.get((project, environment), {})
    return _read


# ---------------------------------------------------------------------------
# _compute
# ---------------------------------------------------------------------------

def test_compute_is_deterministic():
    data = {"B": "2", "A": "1"}
    assert _compute(data) == _compute(data)


def test_compute_order_independent():
    a = {"KEY1": "val1", "KEY2": "val2"}
    b = {"KEY2": "val2", "KEY1": "val1"}
    assert _compute(a) == _compute(b)


def test_compute_differs_for_different_values():
    a = {"KEY": "foo"}
    b = {"KEY": "bar"}
    assert _compute(a) != _compute(b)


def test_compute_empty_dict():
    result = _compute({})
    assert isinstance(result, str)
    assert len(result) == 64  # SHA-256 hex digest length


# ---------------------------------------------------------------------------
# compute_checksum
# ---------------------------------------------------------------------------

def test_compute_checksum_returns_result():
    store = {("myapp", "staging"): {"DB_URL": "postgres://localhost", "PORT": "5432"}}
    read = _make_read(store)
    result = compute_checksum("myapp", "staging", read)
    assert isinstance(result, ChecksumResult)
    assert result.project == "myapp"
    assert result.environment == "staging"
    assert result.key_count == 2
    assert len(result.checksum) == 64


def test_compute_checksum_empty_env():
    read = _make_read({})
    result = compute_checksum("myapp", "dev", read)
    assert result.key_count == 0
    assert isinstance(result.checksum, str)


def test_compute_checksum_to_dict():
    read = _make_read({("p", "e"): {"K": "V"}})
    d = compute_checksum("p", "e", read).to_dict()
    assert d["project"] == "p"
    assert d["environment"] == "e"
    assert "checksum" in d
    assert d["key_count"] == 1


# ---------------------------------------------------------------------------
# verify_checksum
# ---------------------------------------------------------------------------

def test_verify_checksum_matched():
    store = {("app", "prod"): {"SECRET": "abc"}}
    read = _make_read(store)
    expected = compute_checksum("app", "prod", read).checksum
    result = verify_checksum("app", "prod", expected, read)
    assert isinstance(result, VerifyResult)
    assert result.matched is True
    assert result.expected == result.actual


def test_verify_checksum_not_matched():
    store = {("app", "prod"): {"SECRET": "abc"}}
    read = _make_read(store)
    result = verify_checksum("app", "prod", "deadbeef", read)
    assert result.matched is False
    assert result.expected == "deadbeef"
    assert result.actual != "deadbeef"


def test_verify_checksum_to_dict():
    read = _make_read({("p", "e"): {"X": "1"}})
    expected = compute_checksum("p", "e", read).checksum
    d = verify_checksum("p", "e", expected, read).to_dict()
    assert d["matched"] is True
    assert "expected" in d
    assert "actual" in d
