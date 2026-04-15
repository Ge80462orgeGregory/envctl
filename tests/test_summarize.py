"""Tests for envctl.summarize."""

from __future__ import annotations

from typing import Dict

import pytest

from envctl.summarize import summarize_env, SummarizeError, SummaryResult


def _make_read(data: Dict[str, Dict[str, Dict[str, str]]]):
    def _read(project: str, environment: str) -> Dict[str, str]:
        return data.get(project, {}).get(environment, {})
    return _read


_BASE = {
    "myapp": {
        "production": {
            "DATABASE_URL": "postgres://localhost/prod",
            "SECRET_KEY": "s3cr3t",
            "DEBUG": "",
            "API_KEY": "abc123",
        }
    }
}

_read = _make_read(_BASE)


def test_summary_total_keys():
    result = summarize_env("myapp", "production", _read)
    assert result.total_keys == 4


def test_summary_empty_values():
    result = summarize_env("myapp", "production", _read)
    assert result.empty_values == 1


def test_summary_non_empty_values():
    result = summarize_env("myapp", "production", _read)
    assert result.non_empty_values == 3


def test_summary_avg_value_length():
    result = summarize_env("myapp", "production", _read)
    values = ["postgres://localhost/prod", "s3cr3t", "", "abc123"]
    expected = sum(len(v) for v in values) / len(values)
    assert abs(result.avg_value_length - expected) < 0.01


def test_summary_longest_key():
    result = summarize_env("myapp", "production", _read)
    assert result.longest_key == "DATABASE_URL"


def test_summary_shortest_key():
    result = summarize_env("myapp", "production", _read)
    assert result.shortest_key == "DEBUG"


def test_summary_project_and_environment_stored():
    result = summarize_env("myapp", "production", _read)
    assert result.project == "myapp"
    assert result.environment == "production"


def test_summary_keys_list():
    result = summarize_env("myapp", "production", _read)
    assert set(result.keys) == {"DATABASE_URL", "SECRET_KEY", "DEBUG", "API_KEY"}


def test_summary_raises_on_empty_env():
    empty_read = _make_read({})
    with pytest.raises(SummarizeError, match="No variables found"):
        summarize_env("ghost", "staging", empty_read)


def test_to_dict_contains_expected_keys():
    result = summarize_env("myapp", "production", _read)
    d = result.to_dict()
    assert "project" in d
    assert "environment" in d
    assert "total_keys" in d
    assert "empty_values" in d
    assert "non_empty_values" in d
    assert "avg_value_length" in d
    assert "longest_key" in d
    assert "shortest_key" in d


def test_to_dict_avg_value_length_rounded():
    result = summarize_env("myapp", "production", _read)
    d = result.to_dict()
    assert isinstance(d["avg_value_length"], float)
    assert len(str(d["avg_value_length"]).split(".")[-1]) <= 2


def test_summary_single_key_env():
    """A single-key environment should have the same key as both longest and shortest."""
    single_read = _make_read({"myapp": {"staging": {"ONLY_KEY": "value"}}})
    result = summarize_env("myapp", "staging", single_read)
    assert result.total_keys == 1
    assert result.longest_key == "ONLY_KEY"
    assert result.shortest_key == "ONLY_KEY"
    assert result.empty_values == 0
    assert result.non_empty_values == 1
