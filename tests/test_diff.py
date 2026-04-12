"""Tests for envctl.diff module."""

import pytest

from envctl.diff import diff_envs, format_diff


BASE = {
    "DATABASE_URL": "postgres://localhost/dev",
    "DEBUG": "true",
    "SECRET_KEY": "dev-secret",
    "PORT": "8000",
}

TARGET = {
    "DATABASE_URL": "postgres://prod-host/mydb",
    "DEBUG": "false",
    "SECRET_KEY": "dev-secret",
    "NEW_RELIC_KEY": "abc123",
}


@pytest.fixture
def diff_result():
    return diff_envs(BASE, TARGET)


def test_added_keys(diff_result):
    assert "NEW_RELIC_KEY" in diff_result["added"]
    assert diff_result["added"]["NEW_RELIC_KEY"] == "abc123"


def test_removed_keys(diff_result):
    assert "PORT" in diff_result["removed"]
    assert diff_result["removed"]["PORT"] == "8000"


def test_changed_keys(diff_result):
    assert "DATABASE_URL" in diff_result["changed"]
    assert diff_result["changed"]["DATABASE_URL"]["from"] == "postgres://localhost/dev"
    assert diff_result["changed"]["DATABASE_URL"]["to"] == "postgres://prod-host/mydb"
    assert "DEBUG" in diff_result["changed"]


def test_unchanged_keys(diff_result):
    assert "SECRET_KEY" in diff_result["unchanged"]
    assert diff_result["unchanged"]["SECRET_KEY"] == "dev-secret"


def test_identical_envs_all_unchanged():
    result = diff_envs(BASE, BASE)
    assert result["added"] == {}
    assert result["removed"] == {}
    assert result["changed"] == {}
    assert set(result["unchanged"].keys()) == set(BASE.keys())


def test_empty_base():
    result = diff_envs({}, TARGET)
    assert result["added"] == TARGET
    assert result["removed"] == {}
    assert result["changed"] == {}


def test_empty_target():
    result = diff_envs(BASE, {})
    assert result["removed"] == BASE
    assert result["added"] == {}


def test_format_diff_masks_values(diff_result):
    output = format_diff(diff_result, mask_values=True)
    assert "***" in output
    assert "abc123" not in output
    assert "postgres://prod-host" not in output


def test_format_diff_shows_values(diff_result):
    output = format_diff(diff_result, mask_values=False)
    assert "abc123" in output
    assert "postgres://prod-host/mydb" in output


def test_format_diff_no_differences():
    result = diff_envs({"A": "1"}, {"A": "1"})
    output = format_diff(result)
    assert "(no differences)" in output


def test_format_diff_summary_line(diff_result):
    output = format_diff(diff_result, mask_values=False)
    assert "Added:" in output
    assert "Removed:" in output
    assert "Changed:" in output
