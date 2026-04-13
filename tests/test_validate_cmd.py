"""Integration tests for the validate CLI command."""
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from envctl.commands.validate_cmd import validate_cmd
from envctl.validate import ValidationIssue, ValidationResult


@pytest.fixture()
def runner():
    return CliRunner()


def _patch(variables=None, result=None):
    """Helper to patch read_env and validate_env together."""
    variables = variables or {}
    patches = [
        patch("envctl.commands.validate_cmd.load_config", return_value={}),
        patch("envctl.commands.validate_cmd.get_envs_dir", return_value="/fake"),
        patch("envctl.commands.validate_cmd.read_env", return_value=variables),
    ]
    if result is not None:
        patches.append(patch("envctl.commands.validate_cmd.validate_env", return_value=result))
    return patches


def test_validate_cmd_success(runner):
    ok_result = ValidationResult(project="myapp", environment="prod", issues=[])
    with patch("envctl.commands.validate_cmd.load_config", return_value={}), \
         patch("envctl.commands.validate_cmd.get_envs_dir", return_value="/fake"), \
         patch("envctl.commands.validate_cmd.read_env", return_value={"K": "v"}), \
         patch("envctl.commands.validate_cmd.validate_env", return_value=ok_result):
        res = runner.invoke(validate_cmd, ["myapp", "prod"])
    assert res.exit_code == 0
    assert "valid" in res.output


def test_validate_cmd_exits_nonzero_on_error(runner):
    bad_result = ValidationResult(
        project="myapp",
        environment="prod",
        issues=[ValidationIssue(key="1BAD", message="bad key", severity="error")],
    )
    with patch("envctl.commands.validate_cmd.load_config", return_value={}), \
         patch("envctl.commands.validate_cmd.get_envs_dir", return_value="/fake"), \
         patch("envctl.commands.validate_cmd.read_env", return_value={"1BAD": "x"}), \
         patch("envctl.commands.validate_cmd.validate_env", return_value=bad_result):
        res = runner.invoke(validate_cmd, ["myapp", "prod"])
    assert res.exit_code == 1
    assert "error" in res.output


def test_validate_cmd_json_output(runner):
    ok_result = ValidationResult(project="myapp", environment="staging", issues=[])
    with patch("envctl.commands.validate_cmd.load_config", return_value={}), \
         patch("envctl.commands.validate_cmd.get_envs_dir", return_value="/fake"), \
         patch("envctl.commands.validate_cmd.read_env", return_value={"PORT": "3000"}), \
         patch("envctl.commands.validate_cmd.validate_env", return_value=ok_result):
        res = runner.invoke(validate_cmd, ["myapp", "staging", "--json"])
    import json
    data = json.loads(res.output)
    assert data["valid"] is True
    assert data["project"] == "myapp"
    assert data["environment"] == "staging"
    assert data["issues"] == []


def test_validate_cmd_require_flag(runner):
    with patch("envctl.commands.validate_cmd.load_config", return_value={}), \
         patch("envctl.commands.validate_cmd.get_envs_dir", return_value="/fake"), \
         patch("envctl.commands.validate_cmd.read_env", return_value={"PORT": "8080"}) as _re, \
         patch("envctl.commands.validate_cmd.validate_env") as mock_validate:
        mock_validate.return_value = ValidationResult(project="p", environment="e", issues=[])
        runner.invoke(validate_cmd, ["p", "e", "--require", "DATABASE_URL", "--require", "PORT"])
        _, kwargs = mock_validate.call_args
        assert "DATABASE_URL" in kwargs.get("required_keys", [])
        assert "PORT" in kwargs.get("required_keys", [])
