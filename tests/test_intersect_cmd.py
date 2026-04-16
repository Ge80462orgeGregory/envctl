"""Tests for the intersect CLI command."""
import json
import pytest
from click.testing import CliRunner
from unittest.mock import patch
from envctl.commands.intersect_cmd import intersect_cmd
from envctl.intersect import IntersectResult, IntersectError


@pytest.fixture
def runner():
    return CliRunner()


def _fake_result():
    return IntersectResult(
        project="myapp",
        source_env="dev",
        target_env="prod",
        common_keys=["DB_URL", "SECRET"],
        common_with_same_value=["DB_URL"],
        common_with_diff_value=["SECRET"],
    )


class _patch:
    def __init__(self, result=None, exc=None):
        self.result = result
        self.exc = exc

    def __call__(self, fn):
        exc = self.exc
        result = self.result

        def wrapper(runner):
            with patch("envctl.commands.intersect_cmd.load_config", return_value={}):
                with patch("envctl.commands.intersect_cmd.get_envs_dir", return_value="/tmp"):
                    with patch("envctl.commands.intersect_cmd.read_env", return_value={}):
                        with patch("envctl.commands.intersect_cmd.intersect_envs") as mock:
                            if exc:
                                mock.side_effect = exc
                            else:
                                mock.return_value = result or _fake_result()
                            fn(runner, mock)
        return wrapper


@_patch()
def test_intersect_cmd_text_output(runner, mock):
    result = runner.invoke(intersect_cmd, ["myapp", "dev", "prod"])
    assert result.exit_code == 0
    assert "DB_URL" in result.output


@_patch()
def test_intersect_cmd_json_output(runner, mock):
    result = runner.invoke(intersect_cmd, ["myapp", "dev", "prod", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["project"] == "myapp"
    assert "common_keys" in data


@_patch(exc=IntersectError("Environment 'dev' not found"))
def test_intersect_cmd_error(runner, mock):
    result = runner.invoke(intersect_cmd, ["myapp", "dev", "prod"])
    assert result.exit_code != 0
    assert "dev" in result.output


@_patch(result=IntersectResult("p", "a", "b"))
def test_intersect_cmd_no_common(runner, mock):
    result = runner.invoke(intersect_cmd, ["p", "a", "b"])
    assert result.exit_code == 0
    assert "No common keys" in result.output
