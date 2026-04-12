"""Tests for envctl.sync module."""

import pytest
from unittest.mock import patch, call
from envctl.sync import sync_envs, SyncConflict


SOURCE = {"DB_HOST": "localhost", "DB_PORT": "5432", "API_KEY": "abc123"}
TARGET = {"DB_HOST": "prod-host", "DB_PORT": "5432"}


def _make_read(source, target):
    def _read(project, env):
        if env == "staging":
            return dict(source)
        if env == "production":
            return dict(target)
        return {}
    return _read


@patch("envctl.sync.write_env")
@patch("envctl.sync.read_env")
def test_sync_adds_new_keys(mock_read, mock_write):
    mock_read.side_effect = _make_read(SOURCE, TARGET)
    result = sync_envs("myapp", "staging", "production", overwrite=True)
    assert "API_KEY" in result["added"]
    assert mock_write.called


@patch("envctl.sync.write_env")
@patch("envctl.sync.read_env")
def test_sync_updates_conflicting_keys_with_overwrite(mock_read, mock_write):
    mock_read.side_effect = _make_read(SOURCE, TARGET)
    result = sync_envs("myapp", "staging", "production", overwrite=True)
    assert "DB_HOST" in result["updated"]


@patch("envctl.sync.write_env")
@patch("envctl.sync.read_env")
def test_sync_skips_identical_keys(mock_read, mock_write):
    mock_read.side_effect = _make_read(SOURCE, TARGET)
    result = sync_envs("myapp", "staging", "production", overwrite=True)
    assert "DB_PORT" in result["skipped"]


@patch("envctl.sync.write_env")
@patch("envctl.sync.read_env")
def test_sync_raises_on_conflict_without_overwrite(mock_read, mock_write):
    mock_read.side_effect = _make_read(SOURCE, TARGET)
    with pytest.raises(SyncConflict) as exc_info:
        sync_envs("myapp", "staging", "production", overwrite=False)
    assert "DB_HOST" in str(exc_info.value)
    mock_write.assert_not_called()


@patch("envctl.sync.write_env")
@patch("envctl.sync.read_env")
def test_sync_specific_keys_only(mock_read, mock_write):
    mock_read.side_effect = _make_read(SOURCE, TARGET)
    result = sync_envs("myapp", "staging", "production", overwrite=True, keys=["API_KEY"])
    assert result["added"] == ["API_KEY"]
    assert result["updated"] == []


@patch("envctl.sync.write_env")
@patch("envctl.sync.read_env")
def test_sync_key_missing_in_source_is_skipped(mock_read, mock_write):
    mock_read.side_effect = _make_read(SOURCE, TARGET)
    result = sync_envs("myapp", "staging", "production", overwrite=True, keys=["NONEXISTENT"])
    assert "NONEXISTENT" in result["skipped"]


@patch("envctl.sync.write_env")
@patch("envctl.sync.read_env")
def test_sync_writes_merged_env(mock_read, mock_write):
    mock_read.side_effect = _make_read(SOURCE, TARGET)
    sync_envs("myapp", "staging", "production", overwrite=True)
    written_data = mock_write.call_args[0][2]
    assert written_data["API_KEY"] == "abc123"
    assert written_data["DB_HOST"] == "localhost"
    assert written_data["DB_PORT"] == "5432"
