"""Tests for envctl.placeholder module."""

from __future__ import annotations

import pytest

from envctl.placeholder import find_placeholders, PlaceholderError, PlaceholderResult


def _make_read(data: dict[str, dict[str, dict[str, str]]]):
    def _read(project: str, environment: str) -> dict[str, str]:
        return data.get(project, {}).get(environment, {})
    return _read


def test_no_placeholders_returns_empty_result():
    read = _make_read({"proj": {"dev": {"KEY": "value", "PORT": "8080"}}})
    result = find_placeholders("proj", "dev", read)
    assert isinstance(result, PlaceholderResult)
    assert result.total == 0
    assert not result.has_unresolved


def test_detects_curly_brace_placeholder():
    read = _make_read({"proj": {"dev": {"URL": "http://${HOST}:${PORT}"}}})
    result = find_placeholders("proj", "dev", read)
    assert result.total == 1
    match = result.matches[0]
    assert match.key == "URL"
    assert "HOST" in match.placeholders
    assert "PORT" in match.placeholders


def test_detects_bare_dollar_placeholder():
    read = _make_read({"proj": {"dev": {"CONN": "postgres://$USER:$PASS@localhost"}}})
    result = find_placeholders("proj", "dev", read)
    assert result.total == 1
    assert set(result.matches[0].placeholders) == {"USER", "PASS"}


def test_mixed_placeholder_styles():
    read = _make_read({"proj": {"staging": {
        "A": "${FOO}",
        "B": "$BAR",
        "C": "plain",
    }}})
    result = find_placeholders("proj", "staging", read)
    assert result.total == 2
    keys = {m.key for m in result.matches}
    assert keys == {"A", "B"}


def test_empty_environment_returns_no_matches():
    read = _make_read({"proj": {"dev": {}}})
    result = find_placeholders("proj", "dev", read)
    assert result.total == 0


def test_missing_environment_raises_error():
    read = _make_read({"proj": {}})
    # read returns {} for missing env; find_placeholders treats None as error
    # Simulate None return
    def _none_read(p, e):
        return None
    with pytest.raises(PlaceholderError):
        find_placeholders("proj", "missing", _none_read)


def test_to_dict_structure():
    read = _make_read({"proj": {"dev": {"URL": "http://${HOST}"}}})
    result = find_placeholders("proj", "dev", read)
    d = result.to_dict()
    assert d["project"] == "proj"
    assert d["environment"] == "dev"
    assert d["total"] == 1
    assert d["matches"][0]["key"] == "URL"
    assert "HOST" in d["matches"][0]["placeholders"]


def test_multiple_keys_with_placeholders():
    read = _make_read({"p": {"e": {
        "A": "${X}",
        "B": "${Y}",
        "C": "no_placeholder",
    }}})
    result = find_placeholders("p", "e", read)
    assert result.total == 2
    assert result.has_unresolved
