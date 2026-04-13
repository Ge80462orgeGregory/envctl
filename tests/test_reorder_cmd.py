"""Tests for envctl.commands.reorder_cmd."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from envctl.commands.reorder_cmd import reorder_cmd
from envctl.reorder import ReorderError, ReorderResult


@pytest.fixture()
def runner():
    return CliRunner()


def _patch(result=None, exc=None):
    """Patch reorder_env inside the command module."""
    if exc is not None:
        return patch(
            "envctl.commands.reorder_cmd.reorder_env",
            side_effect=exc,
        )
    return patch(
        "envctl.commands.reorder_cmd.reorder_env",
        return_value=result,
    )


_CHANGED_RESULT = ReorderResult(
    project="myapp",
    environment="staging",
    original_order=["ZEBRA", "APPLE"],
    new_order=["APPLE", "ZEBRA"],
)

_UNCHANGED_RESULT = ReorderResult(
    project="myapp",
    environment="staging",
    original_order=["APPLE", "ZEBRA"],
    new_order=["APPLE", "ZEBRA"],
)


def test_reorder_cmd_success(runner):
    with _patch(result=_CHANGED_RESULT):
        out = runner.invoke(reorder_cmd, ["myapp", "staging"])
    assert out.exit_code == 0
    assert "APPLE" in out.output


def test_reorder_cmd_no_change_message(runner):
    with _patch(result=_UNCHANGED_RESULT):
        out = runner.invoke(reorder_cmd, ["myapp", "staging"])
    assert out.exit_code == 0
    assert "already in the desired order" in out.output


def test_reorder_cmd_json_output(runner):
    with _patch(result=_CHANGED_RESULT):
        out = runner.invoke(reorder_cmd, ["myapp", "staging", "--json"])
    assert out.exit_code == 0
    data = json.loads(out.output)
    assert data["changed"] is True
    assert "new_order" in data


def test_reorder_cmd_error_exits_nonzero(runner):
    with _patch(exc=ReorderError("bad keys")):
        out = runner.invoke(reorder_cmd, ["myapp", "staging"])
    assert out.exit_code == 1
    assert "Error" in out.output


def test_reorder_cmd_reverse_flag(runner):
    with patch("envctl.commands.reorder_cmd.reorder_env") as mock_reorder:
        mock_reorder.return_value = _CHANGED_RESULT
        runner.invoke(reorder_cmd, ["myapp", "staging", "--reverse"])
        _, kwargs = mock_reorder.call_args
        assert kwargs["reverse"] is True


def test_reorder_cmd_custom_keys_parsed(runner):
    with patch("envctl.commands.reorder_cmd.reorder_env") as mock_reorder:
        mock_reorder.return_value = _CHANGED_RESULT
        runner.invoke(reorder_cmd, ["myapp", "staging", "--keys", "FOO,BAR"])
        _, kwargs = mock_reorder.call_args
        assert kwargs["key_order"] == ["FOO", "BAR"]
