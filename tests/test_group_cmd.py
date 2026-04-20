"""Tests for the group CLI command."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from envctl.commands.group_cmd import group_cmd
from envctl.group import GroupResult


@pytest.fixture()
def runner():
    return CliRunner()


def _fake_result(**kwargs) -> GroupResult:
    return GroupResult(
        project=kwargs.get("project", "myproject"),
        environment=kwargs.get("environment", "staging"),
        groups=kwargs.get("groups", {"DB": {"DB_HOST": "localhost", "DB_PORT": "5432"}}),
        ungrouped=kwargs.get("ungrouped", {"DEBUG": "true"}),
    )


def _patch(result=None, exc=None):
    if exc:
        return patch("envctl.commands.group_cmd.group_env", side_effect=exc)
    return patch("envctl.commands.group_cmd.group_env", return_value=result or _fake_result())


def test_group_cmd_text_output(runner):
    with _patch():
        out = runner.invoke(group_cmd, ["myproject", "staging"])
    assert out.exit_code == 0
    assert "[DB]" in out.output
    assert "DB_HOST=localhost" in out.output
    assert "[ungrouped]" in out.output
    assert "DEBUG=true" in out.output


def test_group_cmd_json_output(runner):
    with _patch():
        out = runner.invoke(group_cmd, ["myproject", "staging", "--format", "json"])
    assert out.exit_code == 0
    data = json.loads(out.output)
    assert data["project"] == "myproject"
    assert "groups" in data
    assert "ungrouped" in data


def test_group_cmd_with_explicit_prefix(runner):
    with _patch():
        out = runner.invoke(group_cmd, ["myproject", "staging", "--prefix", "DB"])
    assert out.exit_code == 0


def test_group_cmd_error_exits_nonzero(runner):
    from envctl.group import GroupError
    with _patch(exc=GroupError("not found")):
        out = runner.invoke(group_cmd, ["myproject", "missing"])
    assert out.exit_code != 0
    assert "not found" in out.output


def test_group_cmd_no_variables(runner):
    empty = GroupResult(project="p", environment="e", groups={}, ungrouped={})
    with _patch(result=empty):
        out = runner.invoke(group_cmd, ["p", "e"])
    assert out.exit_code == 0
    assert "No variables found" in out.output


def test_group_cmd_summary_line(runner):
    with _patch():
        out = runner.invoke(group_cmd, ["myproject", "staging"])
    assert "group(s)" in out.output
    assert "key(s)" in out.output
