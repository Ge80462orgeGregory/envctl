import json
import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from envctl.commands.mask_cmd import mask_cmd
from envctl.mask import MaskResult, MaskError


@pytest.fixture
def runner():
    return CliRunner()


def _patch(read_return=None, result=None, error=None):
    def decorator(fn):
        def wrapper(*args, **kwargs):
            fake_env = read_return or {"DB_PASSWORD": "secret", "APP_NAME": "myapp"}
            fake_result = result or MaskResult(
                project="myproject",
                environment="staging",
                masked={"DB_PASSWORD": "se****", "APP_NAME": "myapp"},
                masked_keys=["DB_PASSWORD"],
                total_masked=1,
            )
            with patch("envctl.commands.mask_cmd.load_config", return_value={}):
                with patch("envctl.commands.mask_cmd.get_envs_dir", return_value="/tmp/envs"):
                    with patch("envctl.commands.mask_cmd._read", return_value=fake_env):
                        with patch("envctl.commands.mask_cmd._write") as mock_write:
                            if error:
                                with patch("envctl.commands.mask_cmd.mask_env", side_effect=error):
                                    return fn(*args, mock_write=mock_write, **kwargs)
                            else:
                                with patch("envctl.commands.mask_cmd.mask_env", return_value=fake_result):
                                    return fn(*args, mock_write=mock_write, **kwargs)
        return wrapper
    return decorator


def test_mask_cmd_text_output(runner):
    fake_env = {"DB_PASSWORD": "secret", "APP_NAME": "myapp"}
    fake_result = MaskResult(
        project="myproject",
        environment="staging",
        masked={"DB_PASSWORD": "se****", "APP_NAME": "myapp"},
        masked_keys=["DB_PASSWORD"],
        total_masked=1,
    )
    with patch("envctl.commands.mask_cmd.load_config", return_value={}):
        with patch("envctl.commands.mask_cmd.get_envs_dir", return_value="/tmp/envs"):
            with patch("envctl.commands.mask_cmd._read", return_value=fake_env):
                with patch("envctl.commands.mask_cmd._write"):
                    with patch("envctl.commands.mask_cmd.mask_env", return_value=fake_result):
                        result = runner.invoke(mask_cmd, ["myproject", "staging"])
    assert result.exit_code == 0
    assert "Masked 1 key(s)assert "DB_PASSWORD" in result.output


def test_mask_cmd_json_output(runner):
    fake_env = {"DB_PASSWORD": "secret"}
    fake_result = MaskResult(
        project="myproject",
        environment="prod",
        masked={"DB_PASSWORD": "se****"},
        masked_keys=["DB_PASSWORD"],
        total_masked=1,
    )
    with patch("envctl.commands.mask_cmd.load_config", return_value={}):
        with patch("envctl.commands.mask_cmd.get_envs_dir", return_value="/tmp/envs"):
            with patch("envctl.commands.mask_cmd._read", return_value=fake_env):
                with patch("envctl.commands.mask_cmd._write"):
                    with patch("envctl.commands.mask_cmd.mask_env", return_value=fake_result):
                        result = runner.invoke(mask_cmd, ["myproject", "prod", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["total_masked"] == 1
    assert data["project"] == "myproject"


def test_mask_cmd_dry_run_skips_write(runner):
    fake_env = {"SECRET_KEY": "abc123"}
    fake_result = MaskResult(
        project="myproject",
        environment="local",
        masked={"SECRET_KEY": "ab****"},
        masked_keys=["SECRET_KEY"],
        total_masked=1with patch("envctl.commands.mask_cmd.load_config", return_value={}):
        with patch("envctl.commands.mask_cmd.get_envs_dir", return_value="/tmp/envs"):
            with patch("envctl.commands.mask_cmd._read", return_value=fake_env):
                with patch("envctl.commands.mask_cmd._write") as mock_write:
                    with patch("envctl.commands.mask_cmd.mask_env", return_value=fake_result):
                        result = runner.invoke(mask_cmd, ["myproject", "local", "--dry-run"])
    assert result.exit_code == 0
    mock_write.assert_not_called()
    assert "dry run" in result.output


def test_mask_cmd_no_sensitive_keys(runner):
    fake_env = {"APP_NAME": "myapp", "PORT": "8080"}
    fake_result = MaskResult(
        project="myproject",
        environment="staging",
        masked={"APP_NAME": "myapp", "PORT": "8080"},
        masked_keys=[],
        total_masked=0,
    )
    with patch("envctl.commands.mask_cmd.load_config", return_value={}):
        with patch("envctl.commands.mask_cmd.get_envs_dir", return_value="/tmp/envs"):
            with patch("envctl.commands.mask_cmd._read", return_value=fake_env):
                with patch("envctl.commands.mask_cmd._write"):
                    with patch("envctl.commands.mask_cmd.mask_env", return_value=fake_result):
                        result = runner.invoke(mask_cmd, ["myproject", "staging"])
    assert result.exit_code == 0
    assert "No sensitive keys found" in result.output


def test_mask_cmd_error_exits_nonzero(runner):
    with patch("envctl.commands.mask_cmd.load_config", return_value={}):
        with patch("envctl.commands.mask_cmd.get_envs_dir", return_value="/tmp/envs"):
            with patch("envctl.commands.mask_cmd._read", return_value={}):
                with patch("envctl.commands.mask_cmd.mask_env", side_effect=MaskError("something went wrong")):
                    result = runner.invoke(mask_cmd, ["myproject", "staging"])
    assert result.exit_code == 1
    assert "Error" in result.output
