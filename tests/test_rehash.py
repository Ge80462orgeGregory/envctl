"""Tests for envctl.rehash."""

import pytest

from envctl.rehash import RehashError, RehashResult, rehash_env
from envctl.checksum import compute_checksum


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_read(data: dict):
    def _read(project, environment):
        return data.get((project, environment), {})
    return _read


def _make_read_checksums(data: dict):
    def _read(project, environment):
        return data.get((project, environment), {})
    return _read


_written_checksums: dict = {}


def _write_checksums(project, environment, checksums):
    _written_checksums[(project, environment)] = dict(checksums)


def setup_function():
    _written_checksums.clear()


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------

def test_rehash_updates_all_keys_when_no_prior_checksums():
    read = _make_read({("proj", "dev"): {"A": "1", "B": "2"}})
    read_cs = _make_read_checksums({})

    result = rehash_env("proj", "dev", read, read_cs, _write_checksums)

    assert set(result.updated) == {"A", "B"}
    assert result.unchanged == []
    assert result.total_updated == 2
    assert ("proj", "dev") in _written_checksums


def test_rehash_unchanged_keys_not_in_updated():
    variables = {"X": "hello"}
    existing_hash = compute_checksum({"X": "hello"}).checksum
    read = _make_read({("proj", "staging"): variables})
    read_cs = _make_read_checksums({("proj", "staging"): {"X": existing_hash}})

    result = rehash_env("proj", "staging", read, read_cs, _write_checksums)

    assert "X" not in result.updated
    assert "X" in result.unchanged
    assert result.total_updated == 0


def test_rehash_detects_changed_value():
    old_hash = compute_checksum({"KEY": "old"}).checksum
    read = _make_read({("proj", "prod"): {"KEY": "new"}})
    read_cs = _make_read_checksums({("proj", "prod"): {"KEY": old_hash}})

    result = rehash_env("proj", "prod", read, read_cs, _write_checksums)

    assert "KEY" in result.updated
    stored = _written_checksums[("proj", "prod")]
    assert stored["KEY"] != old_hash


def test_rehash_removes_stale_keys():
    stale_hash = compute_checksum({"OLD": "value"}).checksum
    read = _make_read({("proj", "dev"): {"NEW": "value"}})
    read_cs = _make_read_checksums({("proj", "dev"): {"OLD": stale_hash}})

    result = rehash_env("proj", "dev", read, read_cs, _write_checksums)

    stored = _written_checksums[("proj", "dev")]
    assert "OLD" not in stored
    assert "NEW" in stored
    assert "OLD" in result.updated  # stale removal counts as update


def test_rehash_raises_on_empty_environment():
    read = _make_read({})
    read_cs = _make_read_checksums({})

    with pytest.raises(RehashError, match="Cannot rehash an empty environment"):
        rehash_env("proj", "dev", read, read_cs, _write_checksums)


def test_rehash_result_to_dict():
    read = _make_read({("p", "e"): {"Z": "99"}})
    read_cs = _make_read_checksums({})

    result = rehash_env("p", "e", read, read_cs, _write_checksums)
    d = result.to_dict()

    assert d["project"] == "p"
    assert d["environment"] == "e"
    assert "Z" in d["updated"]
    assert d["total_updated"] == 1
