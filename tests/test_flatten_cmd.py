"""Tests for the flatten CLI command."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from click.testing import CliRunner

from envctl.commands.flatten_cmd import flatten_cmd
from envctl.flatten import FlattenError, FlattenResult


@pytest.fixture()
def runner():
    return CliRunner()


def _patch(result=None, side_effect=None):
    """Patch flatten_envs inside the flatten_cmd module."""
    return patch(
        "envctl.commands.flatten_cmd.flatten_envs",
        return_value=result,
        side_effect=side_effect,
    )


def _fake_result(merged=None, conflicts=None, envs=None):
    return FlattenResult(
        project="myapp",
        environments=envs or ["local", "staging"],
        merged=merged or {"DB": "localhost", "PORT": "5432"},
        conflicts=conflicts or {},
    )


def test_flatten_cmd_dotenv_output(runner):
    with _patch(result=_fake_result()):
        result = runner.invoke(
            flatten_cmd, ["myapp", "local", "staging"]
        )
    assert result.exit_code == 0
    assert 'DB="localhost"' in result.output
    assert 'PORT="5432"' in result.output


def test_flatten_cmd_json_output(runner):
    with _patch(result=_fake_result()):
        result = runner.invoke(
            flatten_cmd, ["myapp", "local", "staging", "--format", "json"]
        )
    assert result.exit_code == 0
    assert '"DB"' in result.output
    assert '"localhost"' in result.output


def test_flatten_cmd_warns_on_conflicts(runner):
    merged = {"PORT": "5432", "DB": "staging-db"}
    conflicts = {"DB": [("local", "localhost"), ("staging", "staging-db")]}
    with _patch(result=_fake_result(merged=merged, conflicts=conflicts)):
        result = runner.invoke(
            flatten_cmd, ["myapp", "local", "staging"]
        )
    assert result.exit_code == 0
    assert "conflict" in result.output.lower() or "conflict" in (result.output + "").lower()


def test_flatten_cmd_error_on_missing_env(runner):
    with _patch(side_effect=FlattenError("Environments not found: ghost")):
        result = runner.invoke(
            flatten_cmd, ["myapp", "local", "ghost"]
        )
    assert result.exit_code != 0
    assert "ghost" in result.output


def test_flatten_cmd_skip_conflicts_flag(runner):
    with patch("envctl.commands.flatten_cmd.flatten_envs") as mock_flatten:
        mock_flatten.return_value = _fake_result()
        runner.invoke(
            flatten_cmd, ["myapp", "local", "staging", "--skip-conflicts"]
        )
        _, kwargs = mock_flatten.call_args
        assert kwargs.get("skip_conflicts") is True


def test_flatten_cmd_priority_flag(runner):
    with patch("envctl.commands.flatten_cmd.flatten_envs") as mock_flatten:
        mock_flatten.return_value = _fake_result()
        runner.invoke(
            flatten_cmd, ["myapp", "local", "staging", "--priority", "local"]
        )
        _, kwargs = mock_flatten.call_args
        assert kwargs.get("priority") == "local"
