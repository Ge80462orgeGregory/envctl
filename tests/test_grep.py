"""Tests for envctl.grep"""

from __future__ import annotations

import pytest

from envctl.grep import grep_env, GrepError


STORE = {
    "API_KEY": "secret-abc",
    "DB_HOST": "localhost",
    "DB_PORT": "5432",
    "DEBUG": "true",
    "app_token": "tok_xyz",
}


def _read(project: str, env: str) -> dict:
    return dict(STORE)


def test_grep_matches_key_substring():
    result = grep_env("proj", "dev", "DB", read=_read)
    keys = {m.key for m in result.matches}
    assert "DB_HOST" in keys
    assert "DB_PORT" in keys
    assert "API_KEY" not in keys


def test_grep_matches_value_substring():
    result = grep_env("proj", "dev", "localhost", read=_read)
    assert result.total == 1
    assert result.matches[0].key == "DB_HOST"
    assert result.matches[0].matched_on == "value"


def test_grep_matched_on_both():
    # 'DEBUG' key contains 'true' — but let's use a pattern that hits key and value
    store = {"TOKEN": "TOKEN_VALUE"}
    result = grep_env("p", "e", "TOKEN", read=lambda *_: store)
    assert result.total == 1
    assert result.matches[0].matched_on == "both"


def test_grep_keys_only():
    result = grep_env("proj", "dev", "secret", read=_read, search_keys=True, search_values=False)
    # 'secret' appears in value of API_KEY, not in any key
    assert result.total == 0


def test_grep_values_only():
    result = grep_env("proj", "dev", "secret", read=_read, search_keys=False, search_values=True)
    assert result.total == 1
    assert result.matches[0].key == "API_KEY"


def test_grep_ignore_case():
    result = grep_env("proj", "dev", "app", read=_read, ignore_case=True)
    keys = {m.key for m in result.matches}
    # 'app_token' key matches 'app' case-insensitively
    assert "app_token" in keys


def test_grep_no_match_returns_empty():
    result = grep_env("proj", "dev", "NONEXISTENT", read=_read)
    assert result.total == 0
    assert result.matches == []


def test_grep_invalid_pattern_raises():
    with pytest.raises(GrepError, match="Invalid pattern"):
        grep_env("proj", "dev", "[", read=_read)


def test_grep_no_target_raises():
    with pytest.raises(GrepError):
        grep_env("proj", "dev", "x", read=_read, search_keys=False, search_values=False)


def test_grep_result_to_dict():
    result = grep_env("myproject", "staging", "DB", read=_read)
    d = result.to_dict()
    assert d["project"] == "myproject"
    assert d["environment"] == "staging"
    assert d["pattern"] == "DB"
    assert isinstance(d["matches"], list)
    assert d["total"] == result.total
