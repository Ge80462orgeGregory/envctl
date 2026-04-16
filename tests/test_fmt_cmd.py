"""Integration tests for the `envctl fmt` CLI command."""

from __future__ import annotations

import json
from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner

from envctl.commands.fmt_cmd import fmt_cmd


SAMPLE_VARS = {"API_KEY": "abc123", "PORT": "8080"}


@pytest.fixture()
def runner():
    return CliRunner()


def _patch(variables=None):
    """Patch load_config, get_envs_dir, and read_env."""
    if variables is None:
        variables = SAMPLE_VARS

    def decorator(fn):
        import functools

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            with patch("envctl.commands.fmt_cmd.load_config", return_value={}):
                with patch("envctl.commands.fmt_cmd.get_envs_dir", return_value="/fake"):
                    with patch("envctl.commands.fmt_cmd.read_env", return_value=variables):
                        return fn(*args, **kwargs)

        return wrapper

    return decorator


@_patch()
def test_fmt_cmd_dotenv_output(runner):
    result = runner.invoke(fmt_cmd, ["myapp", "dev", "--style", "dotenv"])
    assert result.exit_code == 0
    assert 'API_KEY="abc123"' in result.output
    assert 'PORT="8080"' in result.output


@_patch()
def test_fmt_cmd_shell_output(runner):
    result = runner.invoke(fmt_cmd, ["myapp", "dev", "--style", "shell"])
    assert result.exit_code == 0
    assert 'export API_KEY="abc123"' in result.output


@_patch()
def test_fmt_cmd_json_output(runner):
    result = runner.invoke(fmt_cmd, ["myapp", "dev", "--style", "json"])
    assert result.exit_code == 0
    parsed = json.loads(result.output.strip())
    assert parsed["API_KEY"] == "abc123"


@_patch()
def test_fmt_cmd_table_output(runner):
    result = runner.invoke(fmt_cmd, ["myapp", "dev", "--style", "table"])
    assert result.exit_code == 0
    assert "KEY" in result.output
    assert "API_KEY" in result.output


@_patch(variables={})
def test_fmt_cmd_empty_env_table(runner):
    result = runner.invoke(fmt_cmd, ["myapp", "dev", "--style", "table"])
    assert result.exit_code == 0
    assert "(no variables)" in result.output


@_patch()
def test_fmt_cmd_writes_to_file(runner, tmp_path):
    out_file = tmp_path / "output.env"
    result = runner.invoke(
        fmt_cmd,
        ["myapp", "dev", "--style", "dotenv", "--output", str(out_file)],
    )
    assert result.exit_code == 0
    assert out_file.exists()
    content = out_file.read_text()
    assert 'API_KEY="abc123"' in content


@_patch()
def test_fmt_cmd_default_style_is_dotenv(runner):
    """Verify that omitting --style defaults to dotenv format."""
    result = runner.invoke(fmt_cmd, ["myapp", "dev"])
    assert result.exit_code == 0
    assert 'API_KEY="abc123"' in result.output
    assert 'PORT="8080"' in result.output
