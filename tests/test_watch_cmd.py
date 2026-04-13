"""Tests for the watch CLI command."""
from unittest.mock import patch, MagicMock
import json

import pytest
from click.testing import CliRunner

from envctl.commands.watch_cmd import watch_cmd
from envctl.watch import WatchSnapshot, WatchResult, WatchError


@pytest.fixture
def runner():
    return CliRunner()


def _patch_take(snap):
    return patch("envctl.commands.watch_cmd.take_watch_snapshot", return_value=snap)


def _patch_compare(result):
    return patch("envctl.commands.watch_cmd.compare_watch_snapshot", return_value=result)


def _patch_sleep():
    return patch("envctl.commands.watch_cmd.time.sleep")


def _patch_config():
    return patch("envctl.commands.watch_cmd.load_config", return_value={})


def test_watch_cmd_once_no_changes(runner):
    snap = WatchSnapshot("proj", "dev", {"K": "v"})
    result_obj = WatchResult("proj", "dev", {"K": "v"}, {"K": "v"}, [])
    with _patch_config(), _patch_take(snap), _patch_compare(result_obj), _patch_sleep():
        result = runner.invoke(watch_cmd, ["proj", "dev", "--once"])
    assert result.exit_code == 0
    assert "Watching" in result.output


def test_watch_cmd_once_with_changes(runner):
    snap = WatchSnapshot("proj", "dev", {"K": "v"})
    result_obj = WatchResult("proj", "dev", {"K": "v"}, {"K": "new"}, ["+K=new"])
    with _patch_config(), _patch_take(snap), _patch_compare(result_obj), _patch_sleep():
        result = runner.invoke(watch_cmd, ["proj", "dev", "--once"])
    assert result.exit_code == 0
    assert "Changes detected" in result.output
    assert "+K=new" in result.output


def test_watch_cmd_json_format(runner):
    snap = WatchSnapshot("proj", "dev", {"K": "v"})
    result_obj = WatchResult("proj", "dev", {"K": "v"}, {"K": "new"}, ["+K=new"])
    with _patch_config(), _patch_take(snap), _patch_compare(result_obj), _patch_sleep():
        result = runner.invoke(watch_cmd, ["proj", "dev", "--once", "--format", "json"])
    assert result.exit_code == 0
    payload = json.loads(result.output.strip())
    assert payload["project"] == "proj"
    assert "+K=new" in payload["diff"]


def test_watch_cmd_error_on_bad_project(runner):
    with _patch_config(), patch("envctl.commands.watch_cmd.take_watch_snapshot", side_effect=WatchError("bad")):
        result = runner.invoke(watch_cmd, ["", "dev", "--once"])
    assert result.exit_code == 1
    assert "Error" in result.output
