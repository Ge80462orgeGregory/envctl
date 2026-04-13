"""Tests for envctl.promote."""

import pytest

from envctl.promote import PromoteError, promote_env


def _make_read(stores):
    def _read(project, env):
        return dict(stores.get((project, env), {}))
    return _read


def _make_write(stores):
    def _write(project, env, data):
        stores[(project, env)] = dict(data)
    return _write


def test_promote_adds_new_keys():
    stores = {
        ("app", "staging"): {"KEY1": "val1", "KEY2": "val2"},
        ("app", "production"): {},
    }
    result = promote_env("app", "staging", "production",
                         read_fn=_make_read(stores), write_fn=_make_write(stores))
    assert result.promoted == {"KEY1": "val1", "KEY2": "val2"}
    assert stores[("app", "production")] == {"KEY1": "val1", "KEY2": "val2"}


def test_promote_skips_identical_keys():
    stores = {
        ("app", "staging"): {"KEY1": "same"},
        ("app", "production"): {"KEY1": "same"},
    }
    result = promote_env("app", "staging", "production",
                         read_fn=_make_read(stores), write_fn=_make_write(stores))
    assert result.skipped == {"KEY1": "same"}
    assert result.promoted == {}


def test_promote_skips_conflicting_without_overwrite():
    stores = {
        ("app", "staging"): {"KEY1": "new_val"},
        ("app", "production"): {"KEY1": "old_val"},
    }
    result = promote_env("app", "staging", "production", overwrite=False,
                         read_fn=_make_read(stores), write_fn=_make_write(stores))
    assert result.skipped == {"KEY1": "new_val"}
    assert stores[("app", "production")] == {"KEY1": "old_val"}


def test_promote_overwrites_conflicting_with_overwrite():
    stores = {
        ("app", "staging"): {"KEY1": "new_val"},
        ("app", "production"): {"KEY1": "old_val"},
    }
    result = promote_env("app", "staging", "production", overwrite=True,
                         read_fn=_make_read(stores), write_fn=_make_write(stores))
    assert result.overwritten == {"KEY1": "new_val"}
    assert stores[("app", "production")] == {"KEY1": "new_val"}


def test_promote_specific_keys():
    stores = {
        ("app", "staging"): {"A": "1", "B": "2", "C": "3"},
        ("app", "production"): {},
    }
    result = promote_env("app", "staging", "production", keys=["A", "C"],
                         read_fn=_make_read(stores), write_fn=_make_write(stores))
    assert result.promoted == {"A": "1", "C": "3"}
    assert stores[("app", "production")] == {"A": "1", "C": "3"}


def test_promote_raises_on_same_env():
    stores = {("app", "staging"): {"A": "1"}}
    with pytest.raises(PromoteError, match="must differ"):
        promote_env("app", "staging", "staging",
                    read_fn=_make_read(stores), write_fn=_make_write(stores))


def test_promote_raises_on_empty_source():
    stores = {("app", "staging"): {}, ("app", "production"): {}}
    with pytest.raises(PromoteError, match="empty or does not exist"):
        promote_env("app", "staging", "production",
                    read_fn=_make_read(stores), write_fn=_make_write(stores))


def test_promote_raises_on_missing_specific_keys():
    stores = {
        ("app", "staging"): {"A": "1"},
        ("app", "production"): {},
    }
    with pytest.raises(PromoteError, match="Keys not found"):
        promote_env("app", "staging", "production", keys=["A", "MISSING"],
                    read_fn=_make_read(stores), write_fn=_make_write(stores))
