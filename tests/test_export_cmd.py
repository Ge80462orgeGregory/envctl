"""Integration tests for the export CLI command."""

import json
import os
import pytest
from click.testing import CliRunner

from envctl.commands.export_cmd import export_cmd


@pytest.fixture()
def runner(tmp_path, monkeypatch):
    """Return a Click test runner with envs dir wired to a temp directory."""
    envs_dir = tmp_path / "envs"
    envs_dir.mkdir()
    project_dir = envs_dir / "myapp"
    project_dir.mkdir()
    env_file = project_dir / "production.env"
    env_file.write_text('DB_HOST="prod-db"\nDB_PORT="5432"\n', encoding="utf-8")

    monkeypatch.setattr(
        "envctl.commands.export_cmd.load_config",
        lambda: {"envs_dir": str(envs_dir)},
    )
    monkeypatch.setattr(
        "envctl.commands.export_cmd.get_envs_dir",
        lambda cfg: str(envs_dir),
    )
    monkeypatch.setattr(
        "envctl.commands.export_cmd.read_env",
        lambda envs_dir, project, env: (
            {"DB_HOST": "prod-db", "DB_PORT": "5432"}
            if project == "myapp" and env == "production"
            else {}
        ),
    )
    return CliRunner(), tmp_path


def test_export_cmd_dotenv_stdout(runner):
    cli, _ = runner
    result = cli.invoke(export_cmd, ["myapp", "production"])
    assert result.exit_code == 0
    assert 'DB_HOST="prod-db"' in result.output


def test_export_cmd_json_format(runner):
    cli, _ = runner
    result = cli.invoke(export_cmd, ["myapp", "production", "--format", "json"])
    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert parsed["DB_HOST"] == "prod-db"


def test_export_cmd_shell_format(runner):
    cli, _ = runner
    result = cli.invoke(export_cmd, ["myapp", "production", "--format", "shell"])
    assert result.exit_code == 0
    assert "export DB_HOST" in result.output


def test_export_cmd_to_file(runner, tmp_path):
    cli, tmp = runner
    out_file = str(tmp / "out.env")
    result = cli.invoke(
        export_cmd, ["myapp", "production", "--output", out_file]
    )
    assert result.exit_code == 0
    assert os.path.exists(out_file)
    content = open(out_file).read()
    assert "DB_HOST" in content


def test_export_cmd_missing_env_exits(runner):
    cli, _ = runner
    result = cli.invoke(export_cmd, ["myapp", "nonexistent"])
    assert result.exit_code == 1
