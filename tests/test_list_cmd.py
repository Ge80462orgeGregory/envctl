"""Integration tests for the list CLI command."""

import json
import pytest
from click.testing import CliRunner

from envctl.commands.list_cmd import list_cmd
from envctl.list_ import ListResult, ListError


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture(autouse=True)
def patch_config(monkeypatch):
    monkeypatch.setattr("envctl.commands.list_cmd.load_config", lambda: {})
    monkeypatch.setattr("envctl.commands.list_cmd.get_envs_dir", lambda c: "/fake")


def test_list_cmd_all_projects(runner, monkeypatch):
    results = [
        ListResult(project="app", entries=["local", "prod"]),
    ]
    monkeypatch.setattr("envctl.commands.list_cmd.list_all", lambda d: results)
    result = runner.invoke(list_cmd, [])
    assert result.exit_code == 0
    assert "[app]" in result.output
    assert "local" in result.output


def test_list_cmd_specific_project(runner, monkeypatch):
    monkeypatch.setattr(
        "envctl.commands.list_cmd.list_project_envs",
        lambda d, p: ListResult(project=p, entries=["staging"]),
    )
    result = runner.invoke(list_cmd, ["myapp"])
    assert result.exit_code == 0
    assert "staging" in result.output


def test_list_cmd_json_output(runner, monkeypatch):
    results = [ListResult(project="app", entries=["local"])]
    monkeypatch.setattr("envctl.commands.list_cmd.list_all", lambda d: results)
    result = runner.invoke(list_cmd, ["--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data[0]["project"] == "app"
    assert data[0]["environments"] == ["local"]


def test_list_cmd_unknown_project_error(runner, monkeypatch):
    monkeypatch.setattr(
        "envctl.commands.list_cmd.list_project_envs",
        lambda d, p: (_ for _ in ()).throw(ListError(f"Project '{p}' not found.")),
    )
    result = runner.invoke(list_cmd, ["ghost"])
    assert result.exit_code != 0
    assert "not found" in result.output


def test_list_cmd_empty_store(runner, monkeypatch):
    monkeypatch.setattr("envctl.commands.list_cmd.list_all", lambda d: [])
    result = runner.invoke(list_cmd, [])
    assert result.exit_code == 0
    assert "No projects found" in result.output
