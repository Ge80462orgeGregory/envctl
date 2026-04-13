"""Tests for envctl.compare."""

import pytest
from envctl.compare import compare_envs, CompareError, CompareResult


def _make_read(stores: dict):
    def _read(project: str, env: str) -> dict:
        return stores.get((project, env), {})
    return _read


SRC = ("myapp", "staging")
TGT = ("myapp", "production")


def test_only_in_source():
    read = _make_read({
        SRC: {"ALPHA": "1", "BETA": "2"},
        TGT: {"ALPHA": "1"},
    })
    result = compare_envs(*SRC, *TGT, read=read)
    assert "BETA" in result.only_in_source
    assert result.only_in_source["BETA"] == "2"


def test_only_in_target():
    read = _make_read({
        SRC: {"ALPHA": "1"},
        TGT: {"ALPHA": "1", "GAMMA": "3"},
    })
    result = compare_envs(*SRC, *TGT, read=read)
    assert "GAMMA" in result.only_in_target
    assert result.only_in_target["GAMMA"] == "3"


def test_differing_values():
    read = _make_read({
        SRC: {"URL": "http://staging.example.com"},
        TGT: {"URL": "http://prod.example.com"},
    })
    result = compare_envs(*SRC, *TGT, read=read)
    assert "URL" in result.differing
    assert result.differing["URL"] == ("http://staging.example.com", "http://prod.example.com")


def test_matching_keys():
    read = _make_read({
        SRC: {"SECRET": "abc123"},
        TGT: {"SECRET": "abc123"},
    })
    result = compare_envs(*SRC, *TGT, read=read)
    assert "SECRET" in result.matching
    assert result.matching["SECRET"] == "abc123"


def test_is_identical_when_all_match():
    read = _make_read({
        SRC: {"A": "1", "B": "2"},
        TGT: {"A": "1", "B": "2"},
    })
    result = compare_envs(*SRC, *TGT, read=read)
    assert result.is_identical is True
    assert result.total_differences == 0


def test_is_not_identical_when_differences_exist():
    read = _make_read({
        SRC: {"A": "1", "B": "old"},
        TGT: {"A": "1", "B": "new"},
    })
    result = compare_envs(*SRC, *TGT, read=read)
    assert result.is_identical is False
    assert result.total_differences == 1


def test_total_differences_counts_all_types():
    read = _make_read({
        SRC: {"ONLY_SRC": "x", "CHANGED": "old"},
        TGT: {"ONLY_TGT": "y", "CHANGED": "new"},
    })
    result = compare_envs(*SRC, *TGT, read=read)
    assert result.total_differences == 3


def test_raises_when_both_empty():
    read = _make_read({})
    with pytest.raises(CompareError):
        compare_envs(*SRC, *TGT, read=read)


def test_cross_project_compare():
    read = _make_read({
        ("projectA", "local"): {"DB": "localhost"},
        ("projectB", "local"): {"DB": "remotehost"},
    })
    result = compare_envs("projectA", "local", "projectB", "local", read=read)
    assert result.source_project == "projectA"
    assert result.target_project == "projectB"
    assert "DB" in result.differing
