"""Tests for envctl.history."""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from envctl.history import (
    HistoryEntry,
    HistoryError,
    _history_file_path,
    record_history,
    read_history,
)

FIXED_TS = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
_now = lambda: FIXED_TS  # noqa: E731


@pytest.fixture()
def tmp_envs(tmp_path: Path) -> str:
    return str(tmp_path)


def test_record_creates_history_file(tmp_envs):
    record_history(tmp_envs, "myapp", "staging", "set", {"KEY": "added"}, _now=_now)
    path = _history_file_path(tmp_envs, "myapp", "staging")
    assert path.exists()


def test_record_returns_entry(tmp_envs):
    entry = record_history(
        tmp_envs, "myapp", "prod", "delete", {"OLD_KEY": "removed"}, _now=_now
    )
    assert isinstance(entry, HistoryEntry)
    assert entry.action == "delete"
    assert entry.project == "myapp"
    assert entry.environment == "prod"
    assert entry.changes == {"OLD_KEY": "removed"}
    assert entry.timestamp == FIXED_TS.isoformat()


def test_record_with_actor(tmp_envs):
    entry = record_history(
        tmp_envs, "myapp", "local", "import", {}, actor="alice", _now=_now
    )
    assert entry.actor == "alice"


def test_record_appends_multiple_entries(tmp_envs):
    for action in ("set", "delete", "rotate"):
        record_history(tmp_envs, "proj", "dev", action, {}, _now=_now)
    path = _history_file_path(tmp_envs, "proj", "dev")
    lines = [l for l in path.read_text().splitlines() if l.strip()]
    assert len(lines) == 3


def test_read_history_returns_newest_first(tmp_envs):
    actions = ["set", "delete", "rotate"]
    for i, action in enumerate(actions):
        ts = datetime(2024, 1, i + 1, tzinfo=timezone.utc)
        record_history(tmp_envs, "p", "e", action, {}, _now=lambda t=ts: t)
    entries = read_history(tmp_envs, "p", "e")
    assert [e.action for e in entries] == list(reversed(actions))


def test_read_history_empty_when_no_file(tmp_envs):
    entries = read_history(tmp_envs, "ghost", "nowhere")
    assert entries == []


def test_read_history_limit(tmp_envs):
    for i in range(5):
        record_history(tmp_envs, "p", "e", f"action{i}", {}, _now=_now)
    entries = read_history(tmp_envs, "p", "e", limit=2)
    assert len(entries) == 2


def test_history_entry_round_trips_json():
    entry = HistoryEntry(
        timestamp="2024-01-01T00:00:00+00:00",
        action="set",
        project="x",
        environment="y",
        changes={"A": "added"},
        actor="bob",
    )
    restored = HistoryEntry.from_dict(entry.to_dict())
    assert restored.actor == "bob"
    assert restored.changes == {"A": "added"}
