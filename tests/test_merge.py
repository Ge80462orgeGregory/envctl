"""Tests for envctl.merge."""
from __future__ import annotations

from typing import Dict

import pytest

from envctl.merge import MergeError, merge_envs


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_read(stores: Dict[str, Dict[str, str]]):
    """Return a read_env stub backed by *stores* keyed by 'project/env'."""
    def _read(project: str, env: str) -> Dict[str, str]:
        return dict(stores.get(f"{project}/{env}", {}))
    return _read


_written: Dict[str, Dict[str, str]] = {}


def _write(project: str, env: str, data: Dict[str, str]) -> None:
    _written[f"{project}/{env}"] = dict(data)


def _read_written(project: str, env: str) -> Dict[str, str]:
    return _written.get(f"{project}/{env}", {})


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_merge_adds_new_keys():
    _written.clear()
    read = _make_read({
        "app/local": {"A": "1"},
        "app/staging": {"B": "2"},
        "app/target": {},
    })
    result = merge_envs("app", "local", "staging", "target", read_env=read, write_env=_write)
    assert "A" in result.added
    assert "B" in result.added
    assert result.total_changes == 2
    assert _read_written("app", "target") == {"A": "1", "B": "2"}


def test_merge_source_b_wins_on_conflict_between_sources():
    _written.clear()
    read = _make_read({
        "app/a": {"KEY": "from_a"},
        "app/b": {"KEY": "from_b"},
        "app/target": {},
    })
    merge_envs("app", "a", "b", "target", read_env=read, write_env=_write)
    assert _read_written("app", "target")["KEY"] == "from_b"


def test_merge_skips_existing_keys_without_overwrite():
    _written.clear()
    read = _make_read({
        "app/a": {"X": "new"},
        "app/b": {},
        "app/target": {"X": "old"},
    })
    result = merge_envs("app", "a", "b", "target", overwrite=False, read_env=read, write_env=_write)
    assert "X" in result.skipped
    assert _read_written("app", "target")["X"] == "old"


def test_merge_overwrites_existing_keys_with_flag():
    _written.clear()
    read = _make_read({
        "app/a": {"X": "new"},
        "app/b": {},
        "app/target": {"X": "old"},
    })
    result = merge_envs("app", "a", "b", "target", overwrite=True, read_env=read, write_env=_write)
    assert "X" in result.overwritten
    assert _read_written("app", "target")["X"] == "new"


def test_merge_specific_keys_only():
    _written.clear()
    read = _make_read({
        "app/a": {"A": "1", "B": "2"},
        "app/b": {},
        "app/target": {},
    })
    result = merge_envs("app", "a", "b", "target", keys=["A"], read_env=read, write_env=_write)
    written = _read_written("app", "target")
    assert "A" in written
    assert "B" not in written
    assert result.total_changes == 1


def test_merge_raises_on_unknown_key():
    _written.clear()
    read = _make_read({
        "app/a": {"A": "1"},
        "app/b": {},
        "app/target": {},
    })
    with pytest.raises(MergeError, match="MISSING"):
        merge_envs("app", "a", "b", "target", keys=["MISSING"], read_env=read, write_env=_write)


def test_merge_identical_values_are_skipped():
    _written.clear()
    read = _make_read({
        "app/a": {"K": "same"},
        "app/b": {},
        "app/target": {"K": "same"},
    })
    result = merge_envs("app", "a", "b", "target", overwrite=True, read_env=read, write_env=_write)
    assert "K" in result.skipped
    assert result.total_changes == 0
