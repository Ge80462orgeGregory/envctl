"""Unit tests for envctl.inspect."""
from __future__ import annotations

from typing import Dict

import pytest

from envctl.inspect import InspectError, InspectResult, inspect_env


def _make_read(data: Dict[str, Dict[str, str]]):
    def _read(project: str, environment: str) -> Dict[str, str]:
        return data.get(project, {}).get(environment, {})
    return _read


# ---------------------------------------------------------------------------
# basic result shape
# ---------------------------------------------------------------------------

def test_inspect_returns_correct_counts():
    read = _make_read({"myapp": {"dev": {"KEY1": "value1", "KEY2": "", "KEY3": "${FOO}"}}})
    result = inspect_env("myapp", "dev", read)
    assert result.total_keys == 3
    assert result.empty_keys == 1
    assert result.placeholder_keys == 1


def test_inspect_result_project_and_environment():
    read = _make_read({"proj": {"staging": {"A": "1"}}})
    result = inspect_env("proj", "staging", read)
    assert result.project == "proj"
    assert result.environment == "staging"


def test_inspect_keys_sorted_alphabetically():
    read = _make_read({"p": {"e": {"ZEBRA": "z", "ALPHA": "a", "MANGO": "m"}}})
    result = inspect_env("p", "e", read)
    assert [k.key for k in result.keys] == ["ALPHA", "MANGO", "ZEBRA"]


# ---------------------------------------------------------------------------
# KeyDetail fields
# ---------------------------------------------------------------------------

def test_key_detail_is_empty_true_for_blank_value():
    read = _make_read({"p": {"e": {"EMPTY_KEY": ""}}})
    result = inspect_env("p", "e", read)
    assert result.keys[0].is_empty is True


def test_key_detail_is_empty_false_for_whitespace_only():
    # whitespace-only is still considered empty
    read = _make_read({"p": {"e": {"WS": "   "}}})
    result = inspect_env("p", "e", read)
    assert result.keys[0].is_empty is True


def test_key_detail_length_matches_value():
    read = _make_read({"p": {"e": {"K": "hello"}}})
    result = inspect_env("p", "e", read)
    assert result.keys[0].length == 5


def test_key_detail_has_placeholder_curly():
    read = _make_read({"p": {"e": {"K": "${MY_VAR}"}}})
    result = inspect_env("p", "e", read)
    assert result.keys[0].has_placeholder is True


def test_key_detail_has_placeholder_double_curly():
    read = _make_read({"p": {"e": {"K": "{{MY_VAR}}"}}})
    result = inspect_env("p", "e", read)
    assert result.keys[0].has_placeholder is True


def test_key_detail_no_placeholder_for_plain_value():
    read = _make_read({"p": {"e": {"K": "plain_value"}}})
    result = inspect_env("p", "e", read)
    assert result.keys[0].has_placeholder is False


# ---------------------------------------------------------------------------
# to_dict
# ---------------------------------------------------------------------------

def test_to_dict_contains_expected_keys():
    read = _make_read({"p": {"e": {"X": "1"}}})
    result = inspect_env("p", "e", read)
    d = result.to_dict()
    assert set(d.keys()) == {"project", "environment", "total_keys", "empty_keys", "placeholder_keys", "keys"}


def test_to_dict_key_detail_fields():
    read = _make_read({"p": {"e": {"X": "hi"}}})
    result = inspect_env("p", "e", read)
    kd = result.to_dict()["keys"][0]
    assert set(kd.keys()) == {"key", "value", "has_placeholder", "is_empty", "length"}


# ---------------------------------------------------------------------------
# empty environment
# ---------------------------------------------------------------------------

def test_inspect_empty_env_returns_zero_counts():
    read = _make_read({"p": {"e": {}}})
    result = inspect_env("p", "e", read)
    assert result.total_keys == 0
    assert result.empty_keys == 0
    assert result.placeholder_keys == 0
    assert result.keys == []
