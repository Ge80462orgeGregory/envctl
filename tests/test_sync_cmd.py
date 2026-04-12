"""Tests for envctl.commands.sync_cmd CLI command."""

import pytest
from click.testing import CliRunner
from unittest.mock import patch
from envctl.commands.sync_cmd import sync_cmd
from envctl.sync import SyncConflict


@pytest.fixture
def runner():
    return CliRunner()


@patch("envctl.commands.sync_cmd.sync_envs")
@patch("envctl.commands.sync_cmd.load_config", return_value={})
def test_sync_cmd_success(mock_cfg, mock_sync, runner):
    mock_sync.return_value = {"added": ["API_KEY"], "updated": [], "skipped": ["DB_PORT"]}
    result = runner.invoke(sync_cmd, ["myapp", "staging", "production"])
    assert result.exit_code == 0
    assert "Added" in result.output
    assert "API_KEY" in result.output


@patch("envctl.commands.sync_cmd.sync_envs")
@patch("envctl.commands.sync_cmd.load_config", return_value={})
def test_sync_cmd_overwrite_flag(mock_cfg, mock_sync, runner):
    mock_sync.return_value = {"added": [], "updated": ["DB_HOST"], "skipped": []}
    result = runner.invoke(sync_cmd, ["myapp", "staging", "production", "--overwrite"])
    assert result.exit_code == 0
    mock_sync.assert_called_once_with(
        project="myapp",
        source_env="staging",
        target_env="production",
        overwrite=True,
        keys=None,
    )


@patch("envctl.commands.sync_cmd.sync_envs")
@patch("envctl.commands.sync_cmd.load_config", return_value={})
def test_sync_cmd_conflict_error(mock_cfg, mock_sync, runner):
    mock_sync.side_effect = SyncConflict("Conflicts detected for keys: DB_HOST")
    result = runner.invoke(sync_cmd, ["myapp", "staging", "production"])
    assert result.exit_code != 0
    assert "Conflicts detected" in result.output


@patch("envctl.commands.sync_cmd.sync_envs")
@patch("envctl.commands.sync_cmd.load_config", return_value={})
def test_sync_cmd_nothing_to_sync(mock_cfg, mock_sync, runner):
    mock_sync.return_value = {"added": [], "updated": [], "skipped": ["DB_PORT"]}
    result = runner.invoke(sync_cmd, ["myapp", "staging", "production"])
    assert "Nothing to sync" in result.output


@patch("envctl.commands.sync_cmd.sync_envs")
@patch("envctl.commands.sync_cmd.load_config", return_value={})
def test_sync_cmd_specific_keys(mock_cfg, mock_sync, runner):
    mock_sync.return_value = {"added": ["API_KEY"], "updated": [], "skipped": []}
    result = runner.invoke(
        sync_cmd, ["myapp", "staging", "production", "--key", "API_KEY"]
    )
    assert result.exit_code == 0
    mock_sync.assert_called_once_with(
        project="myapp",
        source_env="staging",
        target_env="production",
        overwrite=False,
        keys=["API_KEY"],
    )
