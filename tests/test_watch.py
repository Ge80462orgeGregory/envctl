"""Tests for envctl.watch module."""
import pytest
from envctl.watch import take_watch_snapshot, compare_watch_snapshot, WatchError, WatchSnapshot


def _make_read(data: dict):
    def _read(project, environment):
        return data.get((project, environment), {})
    return _read


INITIAL = {"DB_HOST": "localhost", "PORT": "5432"}


def test_take_snapshot_captures_variables():
    read = _make_read({("myapp", "staging"): INITIAL})
    snap = take_watch_snapshot("myapp", "staging", read=read)
    assert snap.project == "myapp"
    assert snap.environment == "staging"
    assert snap.variables == INITIAL


def test_take_snapshot_empty_project_raises():
    with pytest.raises(WatchError):
        take_watch_snapshot("", "staging")


def test_take_snapshot_empty_environment_raises():
    with pytest.raises(WatchError):
        take_watch_snapshot("myapp", "")


def test_compare_no_changes():
    data = {("myapp", "staging"): INITIAL}
    read = _make_read(data)
    snap = WatchSnapshot(project="myapp", environment="staging", variables=dict(INITIAL))
    result = compare_watch_snapshot(snap, read=read)
    assert not result.has_changes
    assert result.diff_lines == []


def test_compare_detects_added_key():
    updated = {**INITIAL, "NEW_KEY": "value"}
    read = _make_read({("myapp", "staging"): updated})
    snap = WatchSnapshot(project="myapp", environment="staging", variables=dict(INITIAL))
    result = compare_watch_snapshot(snap, read=read)
    assert result.has_changes
    assert any("NEW_KEY" in line for line in result.diff_lines)


def test_compare_detects_removed_key():
    updated = {"DB_HOST": "localhost"}
    read = _make_read({("myapp", "staging"): updated})
    snap = WatchSnapshot(project="myapp", environment="staging", variables=dict(INITIAL))
    result = compare_watch_snapshot(snap, read=read)
    assert result.has_changes
    assert any("PORT" in line for line in result.diff_lines)


def test_compare_detects_changed_value():
    updated = {**INITIAL, "PORT": "3306"}
    read = _make_read({("myapp", "staging"): updated})
    snap = WatchSnapshot(project="myapp", environment="staging", variables=dict(INITIAL))
    result = compare_watch_snapshot(snap, read=read)
    assert result.has_changes
    assert any("PORT" in line for line in result.diff_lines)


def test_compare_result_stores_before_and_after():
    updated = {**INITIAL, "PORT": "9999"}
    read = _make_read({("myapp", "staging"): updated})
    snap = WatchSnapshot(project="myapp", environment="staging", variables=dict(INITIAL))
    result = compare_watch_snapshot(snap, read=read)
    assert result.before == INITIAL
    assert result.after == updated
