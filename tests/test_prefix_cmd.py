import json
import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from envctl.commands.prefix_cmd import prefix_cmd
from envctl.prefix import PrefixResult, PrefixError


@pytest.fixture
def runner():
    return CliRunner()


def _patch(add_result=None, strip_result=None, add_error=None, strip_error=None):
    def decorator(fn):
        def wrapper(*args, **kwargs):
            with patch("envctl.commands.prefix_cmd.add_prefix") as mock_add, \
                 patch("envctl.commands.prefix_cmd.strip_prefix") as mock_strip, \
                 patch("envctl.commands.prefix_cmd._read"), \
                 patch("envctl.commands.prefix_cmd._write"):
                if add_error:
                    mock_add.side_effect = add_error
                else:
                    mock_add.return_value = add_result
                if strip_error:
                    mock_strip.side_effect = strip_error
                else:
                    mock_strip.return_value = strip_result
                fn(*args, mock_add=mock_add, mock_strip=mock_strip, **kwargs)
        return wrapper
    return decorator


def test_prefix_add_success(runner):
    result_obj = PrefixResult("myapp", "dev", changed=["FOO", "BAR"], skipped=[])
    with patch("envctl.commands.prefix_cmd.add_prefix", return_value=result_obj), \
         patch("envctl.commands.prefix_cmd._read"), \
         patch("envctl.commands.prefix_cmd._write"):
        out = runner.invoke(prefix_cmd, ["add", "myapp", "dev", "APP_"])
    assert out.exit_code == 0
    assert "2 key(s)" in out.output


def test_prefix_add_no_changes(runner):
    result_obj = PrefixResult("myapp", "dev", changed=[], skipped=["APP_FOO"])
    with patch("envctl.commands.prefix_cmd.add_prefix", return_value=result_obj), \
         patch("envctl.commands.prefix_cmd._read"), \
         patch("envctl.commands.prefix_cmd._write"):
        out = runner.invoke(prefix_cmd, ["add", "myapp", "dev", "APP_"])
    assert out.exit_code == 0
    assert "No keys were updated" in out.output


def test_prefix_add_json_output(runner):
    result_obj = PrefixResult("myapp", "dev", changed=["FOO"], skipped=[])
    with patch("envctl.commands.prefix_cmd.add_prefix", return_value=result_obj), \
         patch("envctl.commands.prefix_cmd._read"), \
         patch("envctl.commands.prefix_cmd._write"):
        out = runner.invoke(prefix_cmd, ["add", "myapp", "dev", "APP_", "--json"])
    assert out.exit_code == 0
    data = json.loads(out.output)
    assert data["total_changed"] == 1


def test_prefix_add_error(runner):
    with patch("envctl.commands.prefix_cmd.add_prefix", side_effect=PrefixError("bad")), \
         patch("envctl.commands.prefix_cmd._read"), \
         patch("envctl.commands.prefix_cmd._write"):
        out = runner.invoke(prefix_cmd, ["add", "myapp", "dev", "APP_"])
    assert out.exit_code != 0
    assert "bad" in out.output


def test_prefix_strip_success(runner):
    result_obj = PrefixResult("myapp", "dev", changed=["APP_FOO"], skipped=[])
    with patch("envctl.commands.prefix_cmd.strip_prefix", return_value=result_obj), \
         patch("envctl.commands.prefix_cmd._read"), \
         patch("envctl.commands.prefix_cmd._write"):
        out = runner.invoke(prefix_cmd, ["strip", "myapp", "dev", "APP_"])
    assert out.exit_code == 0
    assert "1 key(s)" in out.output


def test_prefix_strip_no_matches(runner):
    result_obj = PrefixResult("myapp", "dev", changed=[], skipped=["FOO"])
    with patch("envctl.commands.prefix_cmd.strip_prefix", return_value=result_obj), \
         patch("envctl.commands.prefix_cmd._read"), \
         patch("envctl.commands.prefix_cmd._write"):
        out = runner.invoke(prefix_cmd, ["strip", "myapp", "dev", "APP_"])
    assert out.exit_code == 0
    assert "No keys matched" in out.output
