"""CLI tests for the substitute command."""
from __future__ import annotations

import json
from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner

from envctl.commands.substitute_cmd import substitute_cmd
from envctl.substitute import SubstituteError, SubstituteResult


@pytest.fixture()
def runner():
    return CliRunner()


def _patch(result=None, side_effect=None):
    """Patch substitute_env in the command module."""
    class _Ctx:
        def __init__(self, r=result, se=side_effect):
            self._r = r
            self._se = se

        def __enter__(self):
            self._p = patch(
                "envctl.commands.substitute_cmd.substitute_env",
                return_value=self._r,
                side_effect=self._se,
            )
            self._p2 = patch("envctl.commands.substitute_cmd.read_env", return_value={"K": "v"})
            self._p.start()
            self._p2.start()
            return self

        def __exit__(self, *_):
            self._p.stop()
            self._p2.stop()

    return _Ctx()


def _fake_result(**kwargs):
    defaults = dict(
        project="myapp",
        environment="staging",
        substituted={"DB_URL": "postgres://new"},
        skipped={},
    )
    defaults.update(kwargs)
    r = SubstituteResult(
        project=defaults["project"],
        environment=defaults["environment"],
    )
    r.substituted = defaults["substituted"]
    r.skipped = defaults["skipped"]
    return r


def test_substitute_cmd_text_output(runner):
    result_obj = _fake_result()
    with _patch(result=result_obj):
        res = runner.invoke(substitute_cmd, ["myapp", "staging", "--from-env", "production"])
    assert res.exit_code == 0
    assert "Substituted 1 key(s)" in res.output
    assert "DB_URL" in res.output


def test_substitute_cmd_json_output(runner):
    result_obj = _fake_result()
    with _patch(result=result_obj):
        res = runner.invoke(
            substitute_cmd,
            ["myapp", "staging", "--from-env", "production", "--format", "json"],
        )
    assert res.exit_code == 0
    data = json.loads(res.output)
    assert data["project"] == "myapp"
    assert data["total_substituted"] == 1


def test_substitute_cmd_nothing_substituted(runner):
    result_obj = _fake_result(substituted={}, skipped={"X": "not in source"})
    with _patch(result=result_obj):
        res = runner.invoke(substitute_cmd, ["myapp", "staging", "--from-env", "production"])
    assert res.exit_code == 0
    assert "Nothing substituted" in res.output


def test_substitute_cmd_error_exits_nonzero(runner):
    with _patch(side_effect=SubstituteError("bad project")):
        res = runner.invoke(substitute_cmd, ["myapp", "staging", "--from-env", "production"])
    assert res.exit_code != 0
    assert "Error" in res.output


def test_substitute_cmd_skipped_shown(runner):
    result_obj = _fake_result(
        substituted={"A": "new"},
        skipped={"B": "not in target"},
    )
    with _patch(result=result_obj):
        res = runner.invoke(substitute_cmd, ["myapp", "staging", "--from-env", "production"])
    assert "Skipped 1" in res.output
    assert "not in target" in res.output
