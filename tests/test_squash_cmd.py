import json
import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from envctl.commands.squash_cmd import squash_cmd
from envctl.squash import SquashResult, SquashError


@pytest.fixture
def runner():
    return CliRunner()


def _patch(result=None, error=None):
    def decorator(fn):
        def wrapper(*args, **kwargs):
            with patch("envctl.commands.squash_cmd.load_config", return_value={}) as _lc, \
                 patch("envctl.commands.squash_cmd.get_envs_dir", return_value="/fake") as _gd, \
                 patch("envctl.commands.squash_cmd.squash_envs") as mock_sq:
                if error:
                    mock_sq.side_effect = error
                else:
                    mock_sq.return_value = result
                return fn(*args, mock_sq=mock_sq, **kwargs)
        return wrapper
    return decorator


_fake_result = SquashResult(
    project="myapp",
    sources=["dev", "qa"],
    target="merged",
    merged={"A": "1", "B": "2"},
    conflicts={},
)


def test_squash_cmd_text_output(runner):
    with patch("envctl.commands.squash_cmd.load_config", return_value={}), \
         patch("envctl.commands.squash_cmd.get_envs_dir", return_value="/fake"), \
         patch("envctl.commands.squash_cmd.squash_envs", return_value=_fake_result):
        result = runner.invoke(squash_cmd, ["myapp", "dev", "qa", "--target", "merged"])
    assert result.exit_code == 0
    assert "merged" in result.output
    assert "2" in result.output


def test_squash_cmd_json_output(runner):
    with patch("envctl.commands.squash_cmd.load_config", return_value={}), \
         patch("envctl.commands.squash_cmd.get_envs_dir", return_value="/fake"), \
         patch("envctl.commands.squash_cmd.squash_envs", return_value=_fake_result):
        result = runner.invoke(squash_cmd, ["myapp", "dev", "qa", "--target", "merged", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["target"] == "merged"
    assert data["total_keys"] == 2


def test_squash_cmd_error(runner):
    with patch("envctl.commands.squash_cmd.load_config", return_value={}), \
         patch("envctl.commands.squash_cmd.get_envs_dir", return_value="/fake"), \
         patch("envctl.commands.squash_cmd.squash_envs", side_effect=SquashError("bad input")):
        result = runner.invoke(squash_cmd, ["myapp", "dev", "--target", "merged"])
    assert result.exit_code != 0
    assert "bad input" in result.output
