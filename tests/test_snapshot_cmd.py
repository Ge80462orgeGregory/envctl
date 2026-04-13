"""Integration tests for the snapshot CLI commands."""

from __future__ import annotations

import json
import os

import pytest
from click.testing import CliRunner

from envctl.commands.snapshot_cmd import snapshot_cmd
from envctl.snapshot import Snapshot, SnapshotError


@pytest.fixture()
def runner():
    return CliRunner()


def _patch_take(monkeypatch, snap=None, exc=None):
    def _fake_take(project, label, **_):
        if exc:
            raise exc
        return snap
    monkeypatch.setattr("envctl.commands.snapshot_cmd.take_snapshot", _fake_take)


def _patch_restore(monkeypatch, result=None, exc=None):
    from envctl.snapshot import RestoreResult

    def _fake_restore(snapshot, **_):
        if exc:
            raise exc
        return result or RestoreResult(project="p", label="l", restored_envs=["local"], total_keys=3)
    monkeypatch.setattr("envctl.commands.snapshot_cmd.restore_snapshot", _fake_restore)


# ---------------------------------------------------------------------------
# take
# ---------------------------------------------------------------------------

def test_take_cmd_prints_json(runner, monkeypatch):
    snap = Snapshot(
        project="myapp", label="v1",
        created_at="2024-01-01T00:00:00Z",
        envs={"local": {"A": "1"}},
    )
    _patch_take(monkeypatch, snap=snap)
    result = runner.invoke(snapshot_cmd, ["take", "myapp", "v1"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["project"] == "myapp"
    assert payload["label"] == "v1"
    assert payload["envs"]["local"] == {"A": "1"}


def test_take_cmd_writes_file(runner, monkeypatch, tmp_path):
    snap = Snapshot(
        project="myapp", label="v1",
        created_at="2024-01-01T00:00:00Z",
        envs={"local": {"A": "1"}},
    )
    _patch_take(monkeypatch, snap=snap)
    out_file = str(tmp_path / "snap.json")
    result = runner.invoke(snapshot_cmd, ["take", "myapp", "v1", "--output", out_file])
    assert result.exit_code == 0
    assert os.path.exists(out_file)
    with open(out_file) as fh:
        data = json.load(fh)
    assert data["label"] == "v1"


def test_take_cmd_error_exits_nonzero(runner, monkeypatch):
    _patch_take(monkeypatch, exc=SnapshotError("bad project"))
    result = runner.invoke(snapshot_cmd, ["take", "", "v1"])
    assert result.exit_code != 0
    assert "Error" in result.output


# ---------------------------------------------------------------------------
# restore
# ---------------------------------------------------------------------------

def test_restore_cmd_success(runner, monkeypatch, tmp_path):
    snap_file = tmp_path / "snap.json"
    snap_file.write_text(json.dumps({
        "project": "myapp", "label": "v1",
        "created_at": "2024-01-01T00:00:00Z",
        "envs": {"local": {"A": "1"}},
    }))
    _patch_restore(monkeypatch)
    result = runner.invoke(snapshot_cmd, ["restore", str(snap_file)])
    assert result.exit_code == 0
    assert "Restored" in result.output


def test_restore_cmd_error_exits_nonzero(runner, monkeypatch, tmp_path):
    snap_file = tmp_path / "snap.json"
    snap_file.write_text(json.dumps({
        "project": "myapp", "label": "v1",
        "created_at": "2024-01-01T00:00:00Z",
        "envs": {},
    }))
    _patch_restore(monkeypatch, exc=SnapshotError("no environments"))
    result = runner.invoke(snapshot_cmd, ["restore", str(snap_file)])
    assert result.exit_code != 0
    assert "Error" in result.output
