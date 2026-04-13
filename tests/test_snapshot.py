"""Unit tests for envctl.snapshot."""

from __future__ import annotations

import pytest

from envctl.snapshot import (
    Snapshot,
    SnapshotError,
    RestoreResult,
    take_snapshot,
    restore_snapshot,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_STORE: dict[tuple[str, str], dict[str, str]] = {}


def _make_list(envs: list[str]):
    def _list(project: str) -> list[str]:  # noqa: ARG001
        return envs
    return _list


def _make_read(data: dict[tuple[str, str], dict[str, str]]):
    def _read(project: str, env: str) -> dict[str, str]:
        return dict(data.get((project, env), {}))
    return _read


_written: dict[tuple[str, str], dict[str, str]] = {}


def _write(project: str, env: str, variables: dict[str, str]) -> None:
    _written[(project, env)] = dict(variables)


# ---------------------------------------------------------------------------
# take_snapshot
# ---------------------------------------------------------------------------

def test_take_snapshot_captures_all_envs():
    data = {
        ("myapp", "local"): {"A": "1"},
        ("myapp", "staging"): {"A": "2", "B": "3"},
    }
    snap = take_snapshot(
        "myapp", "v1",
        list_environments_fn=_make_list(["local", "staging"]),
        read_env_fn=_make_read(data),
    )
    assert snap.project == "myapp"
    assert snap.label == "v1"
    assert snap.envs["local"] == {"A": "1"}
    assert snap.envs["staging"] == {"A": "2", "B": "3"}
    assert snap.created_at.endswith("Z")


def test_take_snapshot_empty_project_raises():
    with pytest.raises(SnapshotError, match="project name"):
        take_snapshot("", "v1")


def test_take_snapshot_empty_label_raises():
    with pytest.raises(SnapshotError, match="label"):
        take_snapshot("myapp", "")


def test_take_snapshot_no_envs_returns_empty_dict():
    snap = take_snapshot(
        "myapp", "empty",
        list_environments_fn=_make_list([]),
        read_env_fn=_make_read({}),
    )
    assert snap.envs == {}


# ---------------------------------------------------------------------------
# restore_snapshot
# ---------------------------------------------------------------------------

def test_restore_snapshot_writes_all_envs():
    global _written
    _written = {}
    snap = Snapshot(
        project="myapp",
        label="v1",
        created_at="2024-01-01T00:00:00Z",
        envs={"local": {"X": "10"}, "prod": {"X": "99"}},
    )
    result = restore_snapshot(snap, write_env_fn=_write)
    assert set(result.restored_envs) == {"local", "prod"}
    assert result.total_keys == 2
    assert _written[("myapp", "local")] == {"X": "10"}
    assert _written[("myapp", "prod")] == {"X": "99"}


def test_restore_snapshot_empty_raises():
    snap = Snapshot(project="myapp", label="v1", created_at="2024-01-01T00:00:00Z", envs={})
    with pytest.raises(SnapshotError, match="no environments"):
        restore_snapshot(snap, write_env_fn=_write)


def test_restore_result_fields():
    global _written
    _written = {}
    snap = Snapshot(
        project="proj",
        label="lbl",
        created_at="2024-06-01T12:00:00Z",
        envs={"dev": {"K1": "v1", "K2": "v2"}},
    )
    result = restore_snapshot(snap, write_env_fn=_write)
    assert isinstance(result, RestoreResult)
    assert result.project == "proj"
    assert result.label == "lbl"
    assert result.total_keys == 2
