"""Tests for envctl.group."""

from __future__ import annotations

import pytest

from envctl.group import GroupError, GroupResult, group_env


def _make_read(data: dict):
    def _read(project: str, environment: str):
        return data.get((project, environment))

    return _read


_ENV = {
    "DB_HOST": "localhost",
    "DB_PORT": "5432",
    "DB_NAME": "mydb",
    "AWS_KEY": "AKID",
    "AWS_SECRET": "secret",
    "DEBUG": "true",
}


@pytest.fixture()
def _read():
    return _make_read({("myproject", "staging"): _ENV})


def test_group_auto_detects_prefixes(_read):
    result = group_env("myproject", "staging", _read)
    assert "DB" in result.groups
    assert "AWS" in result.groups


def test_group_keys_assigned_to_correct_group(_read):
    result = group_env("myproject", "staging", _read)
    assert set(result.groups["DB"]) == {"DB_HOST", "DB_PORT", "DB_NAME"}
    assert set(result.groups["AWS"]) == {"AWS_KEY", "AWS_SECRET"}


def test_ungrouped_keys_captured(_read):
    result = group_env("myproject", "staging", _read)
    assert "DEBUG" in result.ungrouped


def test_explicit_prefix_limits_groups(_read):
    result = group_env("myproject", "staging", _read, prefixes=["DB"])
    assert "DB" in result.groups
    assert "AWS" not in result.groups
    assert "AWS_KEY" in result.ungrouped


def test_total_groups(_read):
    result = group_env("myproject", "staging", _read)
    assert result.total_groups() == 2


def test_total_keys(_read):
    result = group_env("myproject", "staging", _read)
    assert result.total_keys() == len(_ENV)


def test_missing_environment_raises():
    read = _make_read({})
    with pytest.raises(GroupError, match="not found"):
        group_env("myproject", "missing", read)


def test_custom_separator():
    data = {
        "APP.HOST": "localhost",
        "APP.PORT": "8080",
        "SOLO": "value",
    }
    read = _make_read({("p", "e"): data})
    result = group_env("p", "e", read, separator=".")
    assert "APP" in result.groups
    assert "SOLO" in result.ungrouped


def test_to_dict_structure(_read):
    result = group_env("myproject", "staging", _read)
    d = result.to_dict()
    assert d["project"] == "myproject"
    assert d["environment"] == "staging"
    assert "groups" in d
    assert "ungrouped" in d
    assert d["total_groups"] == result.total_groups()
    assert d["total_keys"] == result.total_keys()


def test_no_shared_prefixes_all_ungrouped():
    data = {"ALPHA": "1", "BETA": "2", "GAMMA": "3"}
    read = _make_read({("p", "e"): data})
    result = group_env("p", "e", read)
    assert result.total_groups() == 0
    assert len(result.ungrouped) == 3
