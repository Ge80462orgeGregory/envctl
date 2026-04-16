import json
import pytest
from click.testing import CliRunner
from unittest.mock import patch
from envctl.commands.required_cmd import required_cmd
from envctl.required import RequiredResult, RequiredError


@pytest.fixture
def runner():
    return CliRunner()


def _patch(result=None, error=None):
    def decorator(fn):
        def wrapper(*args, **kwargs):
            with patch("envctl.commands.required_cmd.load_config", return_value={}):
                with patch("envctl.commands.required_cmd.get_envs_dir", return_value="/fake"):
                    with patch("envctl.commands.required_cmd.read_env", return_value={}):
                        with patch("envctl.commands.required_cmd.check_required") as mock_check:
                            if error:
                                mock_check.side_effect = error
                            else:
                                mock_check.return_value = result
                            return fn(*args, mock_check=mock_check, **kwargs)
        return wrapper
    return decorator


def _fake_result(satisfied=True, missing=None, present=None):
    return RequiredResult(
        project="proj",
        environment="dev",
        required=["A", "B"],
        missing=missing or [],
        present=present or ["A", "B"],
    )


def test_required_cmd_success(runner):
    result_obj = _fake_result()
    with patch("envctl.commands.required_cmd.load_config", return_value={}), \
         patch("envctl.commands.required_cmd.get_envs_dir", return_value="/fake"), \
         patch("envctl.commands.required_cmd.read_env", return_value={}), \
         patch("envctl.commands.required_cmd.check_required", return_value=result_obj):
        out = runner.invoke(required_cmd, ["proj", "dev", "A", "B"])
    assert out.exit_code == 0
    assert "present" in out.output


def test_required_cmd_missing_keys(runner):
    result_obj = _fake_result(satisfied=False, missing=["B"], present=["A"])
    with patch("envctl.commands.required_cmd.load_config", return_value={}), \
         patch("envctl.commands.required_cmd.get_envs_dir", return_value="/fake"), \
         patch("envctl.commands.required_cmd.read_env", return_value={}), \
         patch("envctl.commands.required_cmd.check_required", return_value=result_obj):
        out = runner.invoke(required_cmd, ["proj", "dev", "A", "B"])
    assert out.exit_code != 0
    assert "B" in out.output


def test_required_cmd_json_output(runner):
    result_obj = _fake_result()
    with patch("envctl.commands.required_cmd.load_config", return_value={}), \
         patch("envctl.commands.required_cmd.get_envs_dir", return_value="/fake"), \
         patch("envctl.commands.required_cmd.read_env", return_value={}), \
         patch("envctl.commands.required_cmd.check_required", return_value=result_obj):
        out = runner.invoke(required_cmd, ["proj", "dev", "A", "B", "--format", "json"])
    assert out.exit_code == 0
    data = json.loads(out.output)
    assert data["satisfied"] is True


def test_required_cmd_error(runner):
    with patch("envctl.commands.required_cmd.load_config", return_value={}), \
         patch("envctl.commands.required_cmd.get_envs_dir", return_value="/fake"), \
         patch("envctl.commands.required_cmd.read_env", return_value={}), \
         patch("envctl.commands.required_cmd.check_required", side_effect=RequiredError("not found")):
        out = runner.invoke(required_cmd, ["proj", "dev", "A"])
    assert "Error" in out.output
