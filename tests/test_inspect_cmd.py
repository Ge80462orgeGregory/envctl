"""CLI integration tests for the inspect command."""
from __future__ import annotations

import json
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from envctl.commands.inspect_cmd import inspect_cmd
from envctl.inspect import InspectError, InspectResult, KeyDetail


@pytest.fixture()
def runner():
    return CliRunner()


def _patch(result=None, exc=None):
    """Patch inspect_env and the config helpers."""
    def decorator(fn):
        def wrapper(*args, **kwargs):
            with patch("envctl.commands.inspect_cmd.load_config", return_value={}):
                with patch("envctl.commands.inspect_cmd.get_envs_dir", return_value="/tmp/envs"):
                    with patch("envctl.commands.inspect_cmd.read_env", return_value={}):
                        with patch(
                            "envctl.commands.inspect_cmd.inspect_env",
                            side_effect=exc if exc else None,
                            return_value=result,
                        ):
                            return fn(*args, **kwargs)
        return wrapper
    return decorator


def _fake_result():
    return InspectResult(
        project="myapp",
        environment="dev",
        total_keys=2,
        empty_keys=1,
        placeholder_keys=0,
        keys=[
            KeyDetail(key="API_KEY", value="secret", has_placeholder=False, is_empty=False, length=6),
            KeyDetail(key="DEBUG", value="", has_placeholder=False, is_empty=True, length=0),
        ],
    )


def test_inspect_cmd_text_output(runner):
    result_obj = _fake_result()
    with patch("envctl.commands.inspect_cmd.load_config", return_value={}), \
         patch("envctl.commands.inspect_cmd.get_envs_dir", return_value="/tmp"), \
         patch("envctl.commands.inspect_cmd.read_env", return_value={}), \
         patch("envctl.commands.inspect_cmd.inspect_env", return_value=result_obj):
        out = runner.invoke(inspect_cmd, ["myapp", "dev"])
    assert out.exit_code == 0
    assert "Total keys  : 2" in out.output
    assert "Empty keys  : 1" in out.output


def test_inspect_cmd_json_output(runner):
    result_obj = _fake_result()
    with patch("envctl.commands.inspect_cmd.load_config", return_value={}), \
         patch("envctl.commands.inspect_cmd.get_envs_dir", return_value="/tmp"), \
         patch("envctl.commands.inspect_cmd.read_env", return_value={}), \
         patch("envctl.commands.inspect_cmd.inspect_env", return_value=result_obj):
        out = runner.invoke(inspect_cmd, ["myapp", "dev", "--format", "json"])
    assert out.exit_code == 0
    data = json.loads(out.output)
    assert data["total_keys"] == 2
    assert data["project"] == "myapp"


def test_inspect_cmd_hides_values_by_default(runner):
    result_obj = _fake_result()
    with patch("envctl.commands.inspect_cmd.load_config", return_value={}), \
         patch("envctl.commands.inspect_cmd.get_envs_dir", return_value="/tmp"), \
         patch("envctl.commands.inspect_cmd.read_env", return_value={}), \
         patch("envctl.commands.inspect_cmd.inspect_env", return_value=result_obj):
        out = runner.invoke(inspect_cmd, ["myapp", "dev", "--format", "json"])
    data = json.loads(out.output)
    for kd in data["keys"]:
        assert kd["value"] == "***"


def test_inspect_cmd_shows_values_with_flag(runner):
    result_obj = _fake_result()
    with patch("envctl.commands.inspect_cmd.load_config", return_value={}), \
         patch("envctl.commands.inspect_cmd.get_envs_dir", return_value="/tmp"), \
         patch("envctl.commands.inspect_cmd.read_env", return_value={}), \
         patch("envctl.commands.inspect_cmd.inspect_env", return_value=result_obj):
        out = runner.invoke(inspect_cmd, ["myapp", "dev", "--format", "json", "--show-values"])
    data = json.loads(out.output)
    values = [kd["value"] for kd in data["keys"]]
    assert "secret" in values


def test_inspect_cmd_error_exits_nonzero(runner):
    with patch("envctl.commands.inspect_cmd.load_config", return_value={}), \
         patch("envctl.commands.inspect_cmd.get_envs_dir", return_value="/tmp"), \
         patch("envctl.commands.inspect_cmd.read_env", return_value={}), \
         patch("envctl.commands.inspect_cmd.inspect_env", side_effect=InspectError("not found")):
        out = runner.invoke(inspect_cmd, ["myapp", "missing"])
    assert out.exit_code != 0
    assert "not found" in out.output
