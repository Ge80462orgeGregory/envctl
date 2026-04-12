"""Tests for envctl.env_store and envctl.config."""

import pytest
from pathlib import Path
from unittest.mock import patch

from envctl import env_store
from envctl.config import DEFAULT_CONFIG


@pytest.fixture()
def tmp_envs_dir(tmp_path: Path):
    """Patch get_envs_dir and load_config to use a temp directory."""
    with patch("envctl.env_store.get_envs_dir", return_value=tmp_path):
        yield tmp_path


class TestReadWriteEnv:
    def test_write_creates_file(self, tmp_envs_dir: Path):
        path = env_store.write_env("myapp", "local", {"DEBUG": "true", "PORT": "8080"})
        assert path.exists()
        assert path.name == "local.env"

    def test_read_returns_variables(self, tmp_envs_dir: Path):
        env_store.write_env("myapp", "staging", {"API_KEY": "abc123", "DB_URL": "postgres://localhost/db"})
        result = env_store.read_env("myapp", "staging")
        assert result["API_KEY"] == "abc123"
        assert result["DB_URL"] == "postgres://localhost/db"

    def test_read_missing_env_returns_empty(self, tmp_envs_dir: Path):
        result = env_store.read_env("nonexistent", "production")
        assert result == {}

    def test_write_overwrites_existing(self, tmp_envs_dir: Path):
        env_store.write_env("myapp", "local", {"KEY": "old"})
        env_store.write_env("myapp", "local", {"KEY": "new"})
        result = env_store.read_env("myapp", "local")
        assert result["KEY"] == "new"
        assert len(result) == 1

    def test_comments_and_blank_lines_ignored(self, tmp_envs_dir: Path):
        path = tmp_envs_dir / "proj" / "local.env"
        path.parent.mkdir(parents=True)
        path.write_text("# comment\n\nFOO=bar\n")
        result = env_store.read_env("proj", "local")
        assert result == {"FOO": "bar"}


class TestListOperations:
    def test_list_projects(self, tmp_envs_dir: Path):
        env_store.write_env("alpha", "local", {})
        env_store.write_env("beta", "local", {})
        projects = env_store.list_projects()
        assert set(projects) == {"alpha", "beta"}

    def test_list_environments(self, tmp_envs_dir: Path):
        env_store.write_env("myapp", "local", {})
        env_store.write_env("myapp", "production", {})
        envs = env_store.list_environments("myapp")
        assert set(envs) == {"local", "production"}

    def test_list_projects_empty(self, tmp_envs_dir: Path):
        assert env_store.list_projects() == []


class TestDeleteEnv:
    def test_delete_existing(self, tmp_envs_dir: Path):
        env_store.write_env("myapp", "staging", {"X": "1"})
        result = env_store.delete_env("myapp", "staging")
        assert result is True
        assert env_store.read_env("myapp", "staging") == {}

    def test_delete_nonexistent_returns_false(self, tmp_envs_dir: Path):
        result = env_store.delete_env("ghost", "local")
        assert result is False
