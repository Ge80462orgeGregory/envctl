"""Tests for envctl.prune."""

import pytest

from envctl.prune import PruneError, PruneResult, prune_env

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_store: dict = {}
_written: dict = {}


def _make_read(data: dict):
    """Return a read_env callable seeded with *data* keyed by (project, env)."""
    def _read(project: str, environment: str):
        return dict(data.get((project, environment), {}))
    return _read


def _write(project: str, environment: str, variables: dict):
    _written[(project, environment)] = dict(variables)


def _read_written(project: str, environment: str) -> dict:
    return _written.get((project, environment), {})


def setup_function():
    _written.clear()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_prune_removes_keys_absent_in_reference():
    read = _make_read({
        ("app", "staging"): {"DB_URL": "s", "SECRET": "x", "STALE_KEY": "old"},
        ("app", "production"): {"DB_URL": "p", "SECRET": "y"},
    })
    result = prune_env("app", "staging", "production", read, _write)
    assert "STALE_KEY" in result.removed_keys
    assert "DB_URL" in result.retained_keys
    assert "SECRET" in result.retained_keys
    assert result.total_removed == 1


def test_prune_writes_updated_env():
    read = _make_read({
        ("app", "staging"): {"A": "1", "B": "2", "C": "3"},
        ("app", "production"): {"A": "a", "B": "b"},
    })
    prune_env("app", "staging", "production", read, _write)
    saved = _read_written("app", "staging")
    assert saved == {"A": "1", "B": "2"}


def test_prune_dry_run_does_not_write():
    read = _make_read({
        ("app", "staging"): {"A": "1", "EXTRA": "x"},
        ("app", "production"): {"A": "a"},
    })
    result = prune_env("app", "staging", "production", read, _write, dry_run=True)
    assert result.total_removed == 1
    assert ("app", "staging") not in _written


def test_prune_nothing_to_remove():
    read = _make_read({
        ("app", "staging"): {"A": "1", "B": "2"},
        ("app", "production"): {"A": "a", "B": "b", "C": "c"},
    })
    result = prune_env("app", "staging", "production", read, _write)
    assert result.total_removed == 0
    assert sorted(result.retained_keys) == ["A", "B"]


def test_prune_raises_when_same_environment():
    read = _make_read({})
    with pytest.raises(PruneError, match="must differ"):
        prune_env("app", "staging", "staging", read, _write)


def test_prune_raises_when_reference_empty():
    read = _make_read({
        ("app", "staging"): {"A": "1"},
        ("app", "production"): {},
    })
    with pytest.raises(PruneError, match="empty"):
        prune_env("app", "staging", "production", read, _write)


def test_prune_result_to_dict():
    read = _make_read({
        ("app", "staging"): {"A": "1", "OLD": "x"},
        ("app", "production"): {"A": "a"},
    })
    result = prune_env("app", "staging", "production", read, _write)
    d = result.to_dict()
    assert d["project"] == "app"
    assert d["environment"] == "staging"
    assert d["reference_environment"] == "production"
    assert d["removed_keys"] == ["OLD"]
    assert d["retained_keys"] == ["A"]
    assert d["total_removed"] == 1
