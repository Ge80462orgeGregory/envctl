"""Tests for envctl.commands.align_cmd."""

import json
import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from envctl.commands.align_cmd import align_cmd
from envctl.align import AlignResult, AlignError


@pytest.fixture
def runner():
    return CliRunner()


def _fake_result(changed=2):
    return AlignResult(
        project="myapp",
        environment="dev",
        original={"A": "hi", "B": "yo"},
        aligned={"A": "hi      ", "B": "yo      "},
        total_changed=changed,
    )


def _patch(result=None, error=None):
    class _Ctx:
        def __enter__(self):
            mock = MagicMock()
            if error:
                mock.side_effect = error
            else:
                mock.return_value = result or _fake_result()
            return mock
        def __exit__(self, *a):
            pass
    return patch("envctl.commands.align_cmd.align_env", _Ctx().__enter__())


def test_align_cmd_text_output(runner):
    result = _fake_result(changed=2)
    with patch("envctl.commands.align_cmd.align_env", return_value=result):
        out = runner.invoke(align_cmd, ["myapp", "dev", "--width", "8"])
    assert out.exit_code == 0
    assert "2" in out.output
    assert "myapp/dev" in out.output


def test_align_cmd_nothing_to_align(runner):
    result = _fake_result(changed=0)
    with patch("envctl.commands.align_cmd.align_env", return_value=result):
        out = runner.invoke(align_cmd, ["myapp", "dev", "--width", "8"])
    assert out.exit_code == 0
    assert "Nothing to align" in out.output


def test_align_cmd_json_output(runner):
    result = _fake_result(changed=1)
    with patch("envctl.commands.align_cmd.align_env", return_value=result):
        out = runner.invoke(align_cmd, ["myapp", "dev", "--width", "8", "--format", "json"])
    assert out.exit_code == 0
    data = json.loads(out.output)
    assert data["project"] == "myapp"
    assert data["total_changed"] == 1


def test_align_cmd_error(runner):
    with patch("envctl.commands.align_cmd.align_env", side_effect=AlignError("bad width")):
        out = runner.invoke(align_cmd, ["myapp", "dev", "--width", "0"])
    assert out.exit_code != 0
    assert "bad width" in out.output


def test_align_cmd_truncate_flag(runner):
    result = _fake_result(changed=1)
    with patch("envctl.commands.align_cmd.align_env", return_value=result) as mock:
        runner.invoke(align_cmd, ["myapp", "dev", "--width", "4", "--truncate"])
        _, kwargs = mock.call_args
        assert kwargs.get("truncate") is True
