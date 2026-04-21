"""Tests for envctl.suffix."""

import pytest
from envctl.suffix import add_suffix, strip_suffix, SuffixError


_store: dict = {}


def _make_read(data: dict):
    def _read(project, environment):
        return dict(data.get((project, environment), {}))
    return _read


def _write(project, environment, data):
    _store[(project, environment)] = dict(data)


def _read_written(project, environment):
    return _store.get((project, environment), {})


def setup_function():
    _store.clear()


# --- add_suffix ---

def test_add_suffix_renames_all_keys():
    _read = _make_read({("proj", "dev"): {"DB_HOST": "localhost", "DB_PORT": "5432"}})
    result = add_suffix("proj", "dev", "_V2", read_fn=_read, write_fn=_write)
    written = _read_written("proj", "dev")
    assert "DB_HOST_V2" in written
    assert "DB_PORT_V2" in written
    assert result.total_changed == 2
    assert result.skipped == []


def test_add_suffix_skips_collision():
    # DB_HOST_V2 already exists, so DB_HOST should be skipped
    _read = _make_read({("proj", "dev"): {"DB_HOST": "localhost", "DB_HOST_V2": "remote"}})
    result = add_suffix("proj", "dev", "_V2", read_fn=_read, write_fn=_write)
    written = _read_written("proj", "dev")
    assert "DB_HOST" in written          # skipped, kept as-is
    assert "DB_HOST_V2" in written       # already existed, renamed from itself
    assert "DB_HOST_V2_V2" not in written
    assert result.skipped == ["DB_HOST"]


def test_add_suffix_empty_suffix_raises():
    _read = _make_read({("proj", "dev"): {"KEY": "val"}})
    with pytest.raises(SuffixError, match="empty"):
        add_suffix("proj", "dev", "", read_fn=_read, write_fn=_write)


def test_add_suffix_empty_env_raises():
    _read = _make_read({})
    with pytest.raises(SuffixError):
        add_suffix("proj", "dev", "_X", read_fn=_read, write_fn=_write)


def test_add_suffix_result_fields():
    _read = _make_read({("proj", "dev"): {"KEY": "value"}})
    result = add_suffix("proj", "dev", "_NEW", read_fn=_read, write_fn=_write)
    assert result.project == "proj"
    assert result.environment == "dev"
    assert result.suffix == "_NEW"
    assert "KEY" in result.changed


# --- strip_suffix ---

def test_strip_suffix_removes_matching_suffix():
    _read = _make_read({("proj", "dev"): {"DB_HOST_V2": "localhost", "DB_PORT_V2": "5432"}})
    result = strip_suffix("proj", "dev", "_V2", read_fn=_read, write_fn=_write)
    written = _read_written("proj", "dev")
    assert "DB_HOST" in written
    assert "DB_PORT" in written
    assert result.total_changed == 2


def test_strip_suffix_leaves_non_matching_keys():
    _read = _make_read({("proj", "dev"): {"DB_HOST_V2": "localhost", "OTHER": "value"}})
    result = strip_suffix("proj", "dev", "_V2", read_fn=_read, write_fn=_write)
    written = _read_written("proj", "dev")
    assert "DB_HOST" in written
    assert "OTHER" in written
    assert result.skipped == ["OTHER"]


def test_strip_suffix_empty_suffix_raises():
    _read = _make_read({("proj", "dev"): {"KEY": "val"}})
    with pytest.raises(SuffixError, match="empty"):
        strip_suffix("proj", "dev", "", read_fn=_read, write_fn=_write)


def test_strip_suffix_empty_env_raises():
    _read = _make_read({})
    with pytest.raises(SuffixError):
        strip_suffix("proj", "dev", "_X", read_fn=_read, write_fn=_write)


def test_strip_suffix_to_dict():
    _read = _make_read({("proj", "dev"): {"KEY_OLD": "val"}})
    result = strip_suffix("proj", "dev", "_OLD", read_fn=_read, write_fn=_write)
    d = result.to_dict()
    assert d["suffix"] == "_OLD"
    assert d["total_changed"] == 1
    assert "KEY_OLD" in d["changed"]
