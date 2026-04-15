"""Tests for envctl.commands.grep_cmd"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from click.testing import CliRunner

from envctl.commands.grep_cmd import grep_cmd
from envctl.grep import GrepResult, GrepMatch, GrepError


@pytest.fixture()
def runner():
    return CliRunner()


def _patch(result=None, side_effect=None):
    return patch(
        "envctl.commands.grep_cmd.grep_env",
        return_value=result,
        side_effect=side_effect,
    )


def _fake_result(matches=None):
    r = GrepResult(project="myapp", environment="dev", pattern="DB")
    if matches:
        r.matches = matches
    return r


def test_grep_cmd_text_no_matches(runner):
    with _patch(result=_fake_result()):
        out = runner.invoke(grep_cmd, ["myapp", "dev", "DB"])
    assert out.exit_code == 0
    assert "No matches found" in out.output


def test_grep_cmd_text_with_matches(runner):
    matches = [GrepMatch(key="DB_HOST", value="localhost", matched_on="key")]
    with _patch(result=_fake_result(matches=matches)):
        out = runner.invoke(grep_cmd, ["myapp", "dev", "DB"])
    assert out.exit_code == 0
    assert "DB_HOST" in out.output
    assert "1 match" in out.output


def test_grep_cmd_json_output(runner):
    matches = [GrepMatch(key="API_KEY", value="secret", matched_on="key")]
    with _patch(result=_fake_result(matches=matches)):
        out = runner.invoke(grep_cmd, ["myapp", "dev", "API", "--format", "json"])
    assert out.exit_code == 0
    import json
    data = json.loads(out.output)
    assert data["project"] == "myapp"
    assert len(data["matches"]) == 1


def test_grep_cmd_error_exits_nonzero(runner):
    with _patch(side_effect=GrepError("bad pattern")):
        out = runner.invoke(grep_cmd, ["myapp", "dev", "["])
    assert out.exit_code == 1
    assert "Error" in out.output


def test_grep_cmd_ignore_case_flag(runner):
    with _patch(result=_fake_result()) as mock:
        runner.invoke(grep_cmd, ["myapp", "dev", "db", "-i"])
    _, kwargs = mock.call_args
    assert kwargs["ignore_case"] is True


def test_grep_cmd_keys_only_flag(runner):
    with _patch(result=_fake_result()) as mock:
        runner.invoke(grep_cmd, ["myapp", "dev", "DB", "--keys-only"])
    _, kwargs = mock.call_args
    assert kwargs["search_keys"] is True
    assert kwargs["search_values"] is False
