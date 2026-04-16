"""Tests for envctl.defaults."""

import pytest
from envctl.defaults import apply_defaults, DefaultsError


def _make_read(store: dict):
    def _read(project, environment):
        return dict(store.get((project, environment), {}))
    return _read


_written = {}


def _write(project, environment, data):
    _written[(project, environment)] = dict(data)


def setup_function():
    _written.clear()


def test_apply_defaults_adds_missing_keys():
    read = _make_read({("proj", "dev"): {"A": "1"}})
    result = apply_defaults("proj", "dev", {"B": "2", "C": "3"}, read, _write)
    assert result.applied == {"B": "2", "C": "3"}
    assert result.skipped == []
    assert _written[("proj", "dev")] == {"A": "1", "B": "2", "C": "3"}


def test_apply_defaults_skips_existing_keys():
    read = _make_read({("proj", "dev"): {"A": "1"}})
    result = apply_defaults("proj", "dev", {"A": "99", "B": "2"}, read, _write)
    assert "A" not in result.applied
    assert "A" in result.skipped
    assert result.applied == {"B": "2"}


def test_apply_defaults_overwrite_replaces_existing():
    read = _make_read({("proj", "dev"): {"A": "old"}})
    result = apply_defaults("proj", "dev", {"A": "new"}, read, _write, overwrite=True)
    assert result.applied == {"A": "new"}
    assert result.skipped == []
    assert _written[("proj", "dev")]["A"] == "new"


def test_apply_defaults_empty_env_applies_all():
    read = _make_read({})
    result = apply_defaults("proj", "staging", {"X": "1", "Y": "2"}, read, _write)
    assert result.total_applied == 2
    assert _written[("proj", "staging")] == {"X": "1", "Y": "2"}


def test_apply_defaults_no_write_when_nothing_applied():
    read = _make_read({("proj", "dev"): {"A": "1"}})
    result = apply_defaults("proj", "dev", {"A": "1"}, read, _write)
    assert result.total_applied == 0
    assert ("proj", "dev") not in _written


def test_apply_defaults_raises_on_empty_project():
    with pytest.raises(DefaultsError, match="project"):
        apply_defaults("", "dev", {"A": "1"}, _make_read({}), _write)


def test_apply_defaults_raises_on_empty_environment():
    with pytest.raises(DefaultsError, match="environment"):
        apply_defaults("proj", "", {"A": "1"}, _make_read({}), _write)


def test_apply_defaults_raises_on_empty_defaults():
    with pytest.raises(DefaultsError, match="defaults"):
        apply_defaults("proj", "dev", {}, _make_read({}), _write)


def test_to_dict_shape():
    read = _make_read({("p", "e"): {}})
    result = apply_defaults("p", "e", {"K": "v"}, read, _write)
    d = result.to_dict()
    assert d["project"] == "p"
    assert d["environment"] == "e"
    assert "applied" in d
    assert "skipped" in d
    assert "total_applied" in d
