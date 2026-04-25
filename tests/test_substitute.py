"""Unit tests for envctl.substitute."""
from __future__ import annotations

import pytest

from envctl.substitute import SubstituteError, SubstituteResult, substitute_env


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
# happy-path tests
# ---------------------------------------------------------------------------

def test_substitute_replaces_existing_key():
    read = _make_read({("proj", "staging"): {"DB_URL": "old", "PORT": "3000"}})
    result = substitute_env(
        project="proj",
        environment="staging",
        source_values={"DB_URL": "new_url"},
        read_env=read,
        write_env=_write,
    )
    assert result.substituted == {"DB_URL": "new_url"}
    assert _read_written("proj", "staging")["DB_URL"] == "new_url"
    assert _read_written("proj", "staging")["PORT"] == "3000"


def test_substitute_skips_key_not_in_target():
    read = _make_read({("proj", "staging"): {"PORT": "3000"}})
    result = substitute_env(
        project="proj",
        environment="staging",
        source_values={"MISSING": "value"},
        read_env=read,
        write_env=_write,
    )
    assert result.total_substituted == 0
    assert "MISSING" in result.skipped
    assert result.skipped["MISSING"] == "not in target"


def test_substitute_skips_key_not_in_source():
    read = _make_read({("proj", "staging"): {"KEY": "val"}})
    result = substitute_env(
        project="proj",
        environment="staging",
        source_values={"OTHER": "x"},
        read_env=read,
        write_env=_write,
        keys=["KEY"],
    )
    assert result.skipped["KEY"] == "not in source"


def test_substitute_no_overwrite_skips_filled_key():
    read = _make_read({("proj", "env"): {"A": "existing"}})
    result = substitute_env(
        project="proj",
        environment="env",
        source_values={"A": "new"},
        read_env=read,
        write_env=_write,
        overwrite=False,
    )
    assert result.total_substituted == 0
    assert result.skipped["A"] == "already has value"


def test_substitute_no_overwrite_fills_empty_value():
    read = _make_read({("proj", "env"): {"A": ""}})
    result = substitute_env(
        project="proj",
        environment="env",
        source_values={"A": "filled"},
        read_env=read,
        write_env=_write,
        overwrite=False,
    )
    assert result.substituted == {"A": "filled"}


def test_substitute_explicit_keys_subset():
    read = _make_read({("proj", "env"): {"A": "1", "B": "2", "C": "3"}})
    result = substitute_env(
        project="proj",
        environment="env",
        source_values={"A": "new_a", "B": "new_b", "C": "new_c"},
        read_env=read,
        write_env=_write,
        keys=["A", "C"],
    )
    assert set(result.substituted.keys()) == {"A", "C"}
    assert _read_written("proj", "env")["B"] == "2"


# ---------------------------------------------------------------------------
# error cases
# ---------------------------------------------------------------------------

def test_substitute_empty_project_raises():
    with pytest.raises(SubstituteError, match="project"):
        substitute_env("", "env", {"K": "v"}, lambda p, e: {}, lambda p, e, d: None)


def test_substitute_empty_environment_raises():
    with pytest.raises(SubstituteError, match="environment"):
        substitute_env("proj", "", {"K": "v"}, lambda p, e: {}, lambda p, e, d: None)


def test_substitute_empty_source_raises():
    with pytest.raises(SubstituteError, match="source_values"):
        substitute_env("proj", "env", {}, lambda p, e: {}, lambda p, e, d: None)


def test_result_to_dict_contains_expected_keys():
    read = _make_read({("p", "e"): {"X": "old"}})
    result = substitute_env(
        project="p",
        environment="e",
        source_values={"X": "new"},
        read_env=read,
        write_env=_write,
    )
    d = result.to_dict()
    assert d["project"] == "p"
    assert d["environment"] == "e"
    assert d["total_substituted"] == 1
    assert "substituted" in d
    assert "skipped" in d
