"""CLI tests for envctl cast command."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from envctl.cast import CastError, CastResult
from envctl.commands.cast_cmd import cast_cmd


@pytest.fixture()
def runner():
    return CliRunner()


def _patch(result: CastResult):
    """Patch cast_env and config helpers."""
    def decorator(fn):
        def wrapper(*args, **kwargs):
            with (
                patch("envctl.commands.cast_cmd.load_config", return_value={}),
                patch("envctl.commands.cast_cmd.get_envs_dir", return_value="/tmp"),
                patch("envctl.commands.cast_cmd.read_env", return_value={}),
                patch("envctl.commands.cast_cmd.write_env"),
                patch("envctl.commands.cast_cmd.cast_env", return_value=result),
            ):
                return fn(*args, **kwargs)
        return wrapper
    return decorator


def _fake_result(**kwargs) -> CastResult:
    defaults = dict(project="app", environment="dev", cast={}, skipped=[], errors=[])
    defaults.update(kwargs)
    return CastResult(**defaults)


def test_cast_cmd_success(runner):
    result_obj = _fake_result(cast={"PORT": "8080"})
    with (
        patch("envctl.commands.cast_cmd.load_config", return_value={}),
        patch("envctl.commands.cast_cmd.get_envs_dir", return_value="/tmp"),
        patch("envctl.commands.cast_cmd.read_env", return_value={}),
        patch("envctl.commands.cast_cmd.write_env"),
        patch("envctl.commands.cast_cmd.cast_env", return_value=result_obj),
    ):
        res = runner.invoke(cast_cmd, ["app", "dev", "-c", "PORT:int"])
    assert res.exit_code == 0
    assert "PORT" in res.output


def test_cast_cmd_json_output(runner):
    result_obj = _fake_result(cast={"PORT": "8080"})
    with (
        patch("envctl.commands.cast_cmd.load_config", return_value={}),
        patch("envctl.commands.cast_cmd.get_envs_dir", return_value="/tmp"),
        patch("envctl.commands.cast_cmd.read_env", return_value={}),
        patch("envctl.commands.cast_cmd.write_env"),
        patch("envctl.commands.cast_cmd.cast_env", return_value=result_obj),
    ):
        res = runner.invoke(cast_cmd, ["app", "dev", "-c", "PORT:int", "--format", "json"])
    assert res.exit_code == 0
    import json
    data = json.loads(res.output)
    assert data["cast"]["PORT"] == "8080"


def test_cast_cmd_invalid_spec(runner):
    with (
        patch("envctl.commands.cast_cmd.load_config", return_value={}),
        patch("envctl.commands.cast_cmd.get_envs_dir", return_value="/tmp"),
    ):
        res = runner.invoke(cast_cmd, ["app", "dev", "-c", "PORTONLY"])
    assert res.exit_code != 0


def test_cast_cmd_cast_error_exits_nonzero(runner):
    with (
        patch("envctl.commands.cast_cmd.load_config", return_value={}),
        patch("envctl.commands.cast_cmd.get_envs_dir", return_value="/tmp"),
        patch("envctl.commands.cast_cmd.read_env", return_value={}),
        patch("envctl.commands.cast_cmd.write_env"),
        patch("envctl.commands.cast_cmd.cast_env", side_effect=CastError("bad type")),
    ):
        res = runner.invoke(cast_cmd, ["app", "dev", "-c", "KEY:uuid"])
    assert res.exit_code != 0
    assert "bad type" in res.output
