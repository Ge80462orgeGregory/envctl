"""Tests for envctl.reorder."""

from __future__ import annotations

from typing import Dict

import pytest

from envctl.reorder import ReorderError, ReorderResult, reorder_env

_STORE: Dict[str, Dict[str, str]] = {}


def _make_read(data: Dict[str, str]):
    def _read(project: str, environment: str) -> Dict[str, str]:
        return dict(data)

    return _read


_written: Dict[str, str] = {}


def _write(project: str, environment: str, variables: Dict[str, str]) -> None:
    _written.clear()
    _written.update(variables)


def _read_written() -> Dict[str, str]:
    return dict(_written)


def setup_function():
    _written.clear()


# ---------------------------------------------------------------------------


def test_reorder_alphabetical():
    data = {"ZEBRA": "1", "APPLE": "2", "MANGO": "3"}
    result = reorder_env(
        "proj", "dev",
        read_env=_make_read(data),
        write_env=_write,
    )
    assert result.new_order == ["APPLE", "MANGO", "ZEBRA"]
    assert list(_read_written().keys()) == ["APPLE", "MANGO", "ZEBRA"]


def test_reorder_reverse():
    data = {"ZEBRA": "1", "APPLE": "2", "MANGO": "3"}
    result = reorder_env(
        "proj", "dev",
        read_env=_make_read(data),
        write_env=_write,
        reverse=True,
    )
    assert result.new_order == ["ZEBRA", "MANGO", "APPLE"]


def test_reorder_custom_key_order():
    data = {"ZEBRA": "1", "APPLE": "2", "MANGO": "3"}
    result = reorder_env(
        "proj", "dev",
        read_env=_make_read(data),
        write_env=_write,
        key_order=["MANGO", "ZEBRA"],
    )
    assert result.new_order == ["MANGO", "ZEBRA", "APPLE"]


def test_reorder_custom_order_unknown_key_raises():
    data = {"APPLE": "1"}
    with pytest.raises(ReorderError, match="GHOST"):
        reorder_env(
            "proj", "dev",
            read_env=_make_read(data),
            write_env=_write,
            key_order=["GHOST"],
        )


def test_reorder_empty_env_raises():
    with pytest.raises(ReorderError):
        reorder_env(
            "proj", "dev",
            read_env=_make_read({}),
            write_env=_write,
        )


def test_reorder_changed_flag_true_when_order_differs():
    data = {"B": "2", "A": "1"}
    result = reorder_env(
        "proj", "dev",
        read_env=_make_read(data),
        write_env=_write,
    )
    assert result.changed is True


def test_reorder_changed_flag_false_when_already_sorted():
    data = {"ALPHA": "1", "BETA": "2", "GAMMA": "3"}
    result = reorder_env(
        "proj", "dev",
        read_env=_make_read(data),
        write_env=_write,
    )
    assert result.changed is False


def test_to_dict_contains_expected_keys():
    data = {"B": "2", "A": "1"}
    result = reorder_env(
        "proj", "dev",
        read_env=_make_read(data),
        write_env=_write,
    )
    d = result.to_dict()
    assert set(d.keys()) == {"project", "environment", "original_order", "new_order", "changed"}
