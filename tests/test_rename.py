"""Tests for envctl.rename and the rename CLI command."""

import pytest
from click.testing import CliRunner
from unittest.mock import MagicMock, patch

from envctl.rename import rename_env, RenameError
from envctl.commands.rename_cmd import rename_cmd


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_store(initial: dict):
    """Return read/write/exists/remove fakes backed by *initial*."""
    store = dict(initial)

    def _read(project, env):
        return store.get((project, env), {})

    def _write(project, env, vars_):
        store[(project, env)] = dict(vars_)

    def _exists(project, env):
        return (project, env) in store

    def _remove(project, env):
        store.pop((project, env), None)

    return store, _read, _write, _exists, _remove


# ---------------------------------------------------------------------------
# Unit tests – rename_env()
# ---------------------------------------------------------------------------

def test_rename_moves_keys():
    store, r, w, e, rm = _make_store({("myapp", "staging"): {"KEY": "val"}})
    result = rename_env("myapp", "staging", "production", "", read_fn=r, write_fn=w, exists_fn=e, remove_fn=rm)
    assert result["keys_moved"] == 1
    assert ("myapp", "production") in store
    assert ("myapp", "staging") not in store


def test_rename_raises_if_src_missing():
    store, r, w, e, rm = _make_store({})
    with pytest.raises(RenameError, match="does not exist"):
        rename_env("myapp", "missing", "production", "", read_fn=r, write_fn=w, exists_fn=e, remove_fn=rm)


def test_rename_raises_if_dst_exists_no_overwrite():
    store, r, w, e, rm = _make_store({
        ("myapp", "staging"): {"A": "1"},
        ("myapp", "production"): {"B": "2"},
    })
    with pytest.raises(RenameError, match="already exists"):
        rename_env("myapp", "staging", "production", "", overwrite=False,
                   read_fn=r, write_fn=w, exists_fn=e, remove_fn=rm)


def test_rename_overwrites_dst_when_flag_set():
    store, r, w, e, rm = _make_store({
        ("myapp", "staging"): {"A": "1"},
        ("myapp", "production"): {"B": "2"},
    })
    result = rename_env("myapp", "staging", "production", "", overwrite=True,
                        read_fn=r, write_fn=w, exists_fn=e, remove_fn=rm)
    assert result["keys_moved"] == 1
    assert store[("myapp", "production")] == {"A": "1"}


# ---------------------------------------------------------------------------
# CLI tests – rename_cmd
# ---------------------------------------------------------------------------

@pytest.fixture()
def runner():
    return CliRunner()


def test_rename_cmd_success(runner):
    with patch("envctl.commands.rename_cmd.load_config"), \
         patch("envctl.commands.rename_cmd.get_envs_dir", return_value="/tmp"), \
         patch("envctl.commands.rename_cmd.rename_env", return_value={"project": "app", "src": "staging", "dst": "prod", "keys_moved": 3}) as mock_rename:
        result = runner.invoke(rename_cmd, ["app", "staging", "prod"])
    assert result.exit_code == 0
    assert "3 key(s) moved" in result.output


def test_rename_cmd_conflict_error(runner):
    with patch("envctl.commands.rename_cmd.load_config"), \
         patch("envctl.commands.rename_cmd.get_envs_dir", return_value="/tmp"), \
         patch("envctl.commands.rename_cmd.rename_env", side_effect=RenameError("already exists")):
        result = runner.invoke(rename_cmd, ["app", "staging", "prod"])
    assert result.exit_code != 0
    assert "already exists" in result.output
