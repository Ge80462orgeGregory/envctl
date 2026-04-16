import json
import pytest
from click.testing import CliRunner
from unittest.mock import patch
from envctl.commands.count_cmd import count_cmd
from envctl.count import CountResult, CountError


@pytest.fixture
def runner():
    return CliRunner()


def _patch(result=None, error=None):
    def decorator(fn):
        def wrapper(*args, **kwargs):
            target = "envctl.commands.count_cmd.count_env"
            if error:
                with patch(target, side_effect=error):
                    return fn(*args, **kwargs)
            with patch(target, return_value=result):
                return fn(*args, **kwargs)
        return wrapper
    return decorator


_fake_result = CountResult(
    project="app",
    environment="dev",
    total=5,
    non_empty=4,
    empty=1,
)


def test_count_cmd_text_output(runner):
    with patch("envctl.commands.count_cmd.count_env", return_value=_fake_result):
        result = runner.invoke(count_cmd, ["app", "dev"])
    assert result.exit_code == 0
    assert "Total keys:  5" in result.output
    assert "Non-empty:   4" in result.output
    assert "Empty:       1" in result.output


def test_count_cmd_json_output(runner):
    with patch("envctl.commands.count_cmd.count_env", return_value=_fake_result):
        result = runner.invoke(count_cmd, ["app", "dev", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["total"] == 5
    assert data["non_empty"] == 4
    assert data["empty"] == 1


def test_count_cmd_error(runner):
    with patch("envctl.commands.count_cmd.count_env", side_effect=CountError("bad project")):
        result = runner.invoke(count_cmd, ["app", "dev"])
    assert result.exit_code != 0
    assert "bad project" in result.output
