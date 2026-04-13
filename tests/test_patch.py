"""Tests for envctl.patch."""

import pytest
from envctl.patch import PatchError, PatchResult, patch_env


_store: dict = {}


def _make_read(data: dict):
    def _read(project, environment):
        return dict(data.get((project, environment), {}))
    return _read


def _write(project, environment, variables):
    _store[(project, environment)] = dict(variables)


def _read_written(project, environment):
    return dict(_store.get((project, environment), {}))


def setup_function():
    _store.clear()


# ---------------------------------------------------------------------------
# set_vars
# ---------------------------------------------------------------------------

def test_patch_sets_new_keys():
    _read = _make_read({("proj", "dev"): {"A": "1"}})
    result = patch_env("proj", "dev", set_vars={"B": "2"}, _read=_read, _write=_write)
    assert "B" in result.set_keys
    assert _read_written("proj", "dev")["B"] == "2"


def test_patch_overwrites_existing_key_by_default():
    _read = _make_read({("proj", "dev"): {"A": "old"}})
    result = patch_env("proj", "dev", set_vars={"A": "new"}, _read=_read, _write=_write)
    assert "A" in result.set_keys
    assert _read_written("proj", "dev")["A"] == "new"


def test_patch_skips_existing_key_when_no_overwrite():
    _read = _make_read({("proj", "dev"): {"A": "old"}})
    result = patch_env(
        "proj", "dev", set_vars={"A": "new"}, overwrite=False, _read=_read, _write=_write
    )
    assert "A" in result.skipped_keys
    assert _read_written("proj", "dev")["A"] == "old"


# ---------------------------------------------------------------------------
# unset_keys
# ---------------------------------------------------------------------------

def test_patch_unsets_existing_key():
    _read = _make_read({("proj", "dev"): {"A": "1", "B": "2"}})
    result = patch_env("proj", "dev", unset_keys=["A"], _read=_read, _write=_write)
    assert "A" in result.unset_keys
    assert "A" not in _read_written("proj", "dev")
    assert _read_written("proj", "dev")["B"] == "2"


def test_patch_skips_missing_key_on_unset():
    _read = _make_read({("proj", "dev"): {"A": "1"}})
    result = patch_env("proj", "dev", unset_keys=["MISSING"], _read=_read, _write=_write)
    assert "MISSING" in result.skipped_keys
    assert result.unset_keys == []


# ---------------------------------------------------------------------------
# combined
# ---------------------------------------------------------------------------

def test_patch_set_and_unset_():
    _read = _make_read({("proj", "dev"): {"A": "1", "B": "2"}})
    result = patch_env(
        "proj", "dev", set_vars={"C": "3"}, unset_keys=["A"], _read=_read, _write=_write
    )
    written = _read_written("proj", "dev")
    assert "C" in result.set_keys
    assert "A" in result.unset_keys
    assert written == {"B": "2", "C": "3"}
    assert result.total_changes == 2


# ---------------------------------------------------------------------------
# error cases
# ---------------------------------------------------------------------------

def test_patch_raises_when_nothing_to_do():
    _read = _make_read({("proj", "dev"): {}})
    with pytest.raises(PatchError):
        patch_env("proj", "dev", _read=_read, _write=_write)


def test_patch_result_total_changes():
    _read = _make_read({("proj", "dev"): {"X": "1"}})
    result = patch_env(
        "proj", "dev", set_vars={"Y": "2", "Z": "3"}, unset_keys=["X"],
        _read=_read, _write=_write,
    )
    assert result.total_changes == 3
