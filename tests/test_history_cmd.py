"""Tests for the history CLI command."""

from unittest.mock import patch

import pytest
from click.testing import CliRunner

from envctl.commands.history_cmd import history_cmd
from envctl.history import HistoryEntry


@pytest.fixture()
def runner():
    return CliRunner()


def _patch(entries=None, envs_dir="/fake"):
    def _decorator(fn):
        import functools

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            with patch("envctl.commands.history_cmd.load_config", return_value={}):
                with patch(
                    "envctl.commands.history_cmd.get_envs_dir", return_value=envs_dir
                ):
                    with patch(
                        "envctl.commands.history_cmd.read_history",
                        return_value=entries or [],
                    ):
                        return fn(*args, **kwargs)

        return wrapper

    return _decorator


_ENTRIES = [
    HistoryEntry(
        timestamp="2024-06-01T12:00:00+00:00",
        action="set",
        project="myapp",
        environment="staging",
        changes={"API_KEY": "added"},
        actor="alice",
    )
]


@_patch(entries=_ENTRIES)
def test_history_cmd_text_output(runner):
    result = runner.invoke(history_cmd, ["myapp", "staging"])
    assert result.exit_code == 0
    assert "SET" in result.output
    assert "alice" in result.output
    assert "API_KEY" in result.output


@_patch(entries=_ENTRIES)
def test_history_cmd_json_output(runner):
    import json

    result = runner.invoke(history_cmd, ["myapp", "staging", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert data[0]["action"] == "set"
    assert data[0]["actor"] == "alice"


@_patch(entries=[])
def test_history_cmd_no_entries(runner):
    result = runner.invoke(history_cmd, ["myapp", "prod"])
    assert result.exit_code == 0
    assert "No history found" in result.output


@_patch(entries=_ENTRIES)
def test_history_cmd_limit_flag(runner):
    result = runner.invoke(history_cmd, ["myapp", "staging", "-n", "1"])
    assert result.exit_code == 0
