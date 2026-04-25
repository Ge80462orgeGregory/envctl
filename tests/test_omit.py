"""Tests for envctl.omit."""

from __future__ import annotations

import pytest

from envctl.omit import OmitError, OmitResult, omit_env

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_store: dict = {}


def _make_read(data: dict):
    def _read(project: str, env: str) -> dict:
        return dict(data.get((project, env), {}))
    return _read


def _write(project: str, env: str, variables: dict) -> None:
    _store[(project, env)] = dict(variables)


def _read_written(project: str, env: str) -> dict:
    return dict(_store.get((project, env), {}))


def setup_function():
    _store.clear()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_omit_removes_existing_key():
    data = {"A": "1", "B": "2", "C": "3"}
    result = omit_env("proj", "dev", ["B"], _make_read({("proj", "dev"): data}), _write)
    assert "B" not in _read_written("proj", "dev")
    assert result.removed == ["B"]
    assert result.not_found == []


def test_omit_removes_multiple_keys():
    data = {"X": "x", "Y": "y", "Z": "z"}
    result = omit_env("proj", "dev", ["X", "Z"], _make_read({("proj", "dev"): data}), _write)
    remaining = _read_written("proj", "dev")
    assert remaining == {"Y": "y"}
    assert sorted(result.removed) == ["X", "Z"]


def test_omit_records_missing_keys():
    data = {"A": "1"}
    result = omit_env("proj", "dev", ["A", "MISSING"], _make_read({("proj", "dev"): data}), _write)
    assert result.removed == ["A"]
    assert result.not_found == ["MISSING"]


def test_omit_all_keys_missing():
    data = {"A": "1"}
    result = omit_env("proj", "dev", ["B", "C"], _make_read({("proj", "dev"): data}), _write)
    assert result.removed == []
    assert result.not_found == ["B", "C"]
    assert _read_written("proj", "dev") == {"A": "1"}


def test_omit_raises_on_empty_keys():
    with pytest.raises(OmitError):
        omit_env("proj", "dev", [], _make_read({}), _write)


def test_omit_total_removed():
    data = {"K1": "v1", "K2": "v2", "K3": "v3"}
    result = omit_env("p", "e", ["K1", "K2"], _make_read({("p", "e"): data}), _write)
    assert result.total_removed == 2


def test_omit_result_to_dict():
    data = {"FOO": "bar"}
    result = omit_env("myproject", "staging", ["FOO"], _make_read({("myproject", "staging"): data}), _write)
    d = result.to_dict()
    assert d["project"] == "myproject"
    assert d["environment"] == "staging"
    assert d["removed"] == ["FOO"]
    assert d["not_found"] == []
    assert d["total_removed"] == 1


def test_omit_does_not_mutate_other_envs():
    shared_data = {
        ("proj", "dev"): {"A": "1", "B": "2"},
        ("proj", "prod"): {"A": "1", "B": "2"},
    }
    omit_env("proj", "dev", ["A"], _make_read(shared_data), _write)
    # prod was never written, so _store should not contain it
    assert ("proj", "prod") not in _store
