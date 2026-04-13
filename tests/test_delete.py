"""Tests for envctl.delete and the delete CLI command."""

import pytest
from click.testing import CliRunner

from envctl.delete import DeleteError, delete_env_or_keys
from envctl.commands.delete_cmd import delete_cmd


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_store(data: dict):
    """Return injectable store helpers backed by *data*."""
    store = {k: dict(v) for k, v in data.items()}  # shallow copy per env

    def _list(project):
        return list(store.keys())

    def _read(project, env):
        return dict(store.get(env, {}))

    def _write(project, env, variables):
        store[env] = dict(variables)

    def _delete(project, env):
        store.pop(env, None)

    return _list, _read, _write, _delete, store


# ---------------------------------------------------------------------------
# Unit tests — delete_env_or_keys
# ---------------------------------------------------------------------------

def test_delete_entire_env():
    _list, _read, _write, _delete, store = _make_store({"staging": {"A": "1"}})
    result = delete_env_or_keys(
        "proj", "staging",
        store_read=_read, store_write=_write,
        store_delete=_delete, store_list=_list,
    )
    assert result == {"removed_keys": [], "deleted_env": True}
    assert "staging" not in store


def test_delete_specific_keys():
    _list, _read, _write, _delete, store = _make_store(
        {"prod": {"A": "1", "B": "2", "C": "3"}}
    )
    result = delete_env_or_keys(
        "proj", "prod", keys=["A", "B"],
        store_read=_read, store_write=_write,
        store_delete=_delete, store_list=_list,
    )
    assert result == {"removed_keys": ["A", "B"], "deleted_env": False}
    assert store["prod"] == {"C": "3"}


def test_delete_missing_env_raises():
    _list, _read, _write, _delete, _ = _make_store({})
    with pytest.raises(DeleteError, match="not found"):
        delete_env_or_keys(
            "proj", "ghost",
            store_read=_read, store_write=_write,
            store_delete=_delete, store_list=_list,
        )


def test_delete_missing_key_raises():
    _list, _read, _write, _delete, _ = _make_store({"dev": {"X": "1"}})
    with pytest.raises(DeleteError, match="NOPE"):
        delete_env_or_keys(
            "proj", "dev", keys=["NOPE"],
            store_read=_read, store_write=_write,
            store_delete=_delete, store_list=_list,
        )


# ---------------------------------------------------------------------------
# CLI tests — delete_cmd
# ---------------------------------------------------------------------------

@pytest.fixture
def runner():
    return CliRunner()


def test_delete_cmd_entire_env(runner, monkeypatch):
    monkeypatch.setattr(
        "envctl.commands.delete_cmd.delete_env_or_keys",
        lambda *a, **kw: {"removed_keys": [], "deleted_env": True},
    )
    result = runner.invoke(delete_cmd, ["myapp", "staging", "--yes"])
    assert result.exit_code == 0
    assert "Deleted environment" in result.output


def test_delete_cmd_specific_key(runner, monkeypatch):
    monkeypatch.setattr(
        "envctl.commands.delete_cmd.delete_env_or_keys",
        lambda *a, **kw: {"removed_keys": ["DB_URL"], "deleted_env": False},
    )
    result = runner.invoke(delete_cmd, ["myapp", "prod", "-k", "DB_URL", "--yes"])
    assert result.exit_code == 0
    assert "DB_URL" in result.output


def test_delete_cmd_error(runner, monkeypatch):
    def _raise(*a, **kw):
        raise DeleteError("boom")

    monkeypatch.setattr("envctl.commands.delete_cmd.delete_env_or_keys", _raise)
    result = runner.invoke(delete_cmd, ["myapp", "ghost", "--yes"])
    assert result.exit_code != 0
    assert "boom" in result.output
