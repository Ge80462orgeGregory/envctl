"""Tests for envctl.tag module."""

import pytest

from envctl.tag import (
    TagError,
    TagResult,
    add_tags,
    list_tags,
    remove_tags,
    _TAGS_KEY,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_store: dict = {}


def _make_read(data: dict):
    def _read(project, environment):
        return dict(data.get((project, environment), {}))
    return _read


def _write(project, environment, data):
    _store[(project, environment)] = dict(data)


def _read_written(project, environment):
    return dict(_store.get((project, environment), {}))


@pytest.fixture(autouse=True)
def clear_store():
    _store.clear()
    yield
    _store.clear()


# ---------------------------------------------------------------------------
# add_tags
# ---------------------------------------------------------------------------

def test_add_tags_to_empty_env():
    read = _make_read({("proj", "dev"): {"KEY": "val"}})
    result = add_tags("proj", "dev", ["release", "stable"], read_fn=read, write_fn=_write)
    assert isinstance(result, TagResult)
    assert "release" in result.tags
    assert "stable" in result.tags


def test_add_tags_merges_with_existing():
    existing = {"KEY": "val", _TAGS_KEY: "alpha"}
    read = _make_read({("proj", "dev"): existing})
    result = add_tags("proj", "dev", ["beta"], read_fn=read, write_fn=_write)
    assert "alpha" in result.tags
    assert "beta" in result.tags


def test_add_tags_deduplicates():
    existing = {_TAGS_KEY: "foo,bar"}
    read = _make_read({("proj", "dev"): existing})
    result = add_tags("proj", "dev", ["foo", "baz"], read_fn=read, write_fn=_write)
    assert result.tags.count("foo") == 1


def test_add_tags_raises_on_empty_list():
    read = _make_read({("proj", "dev"): {}})
    with pytest.raises(TagError):
        add_tags("proj", "dev", [], read_fn=read, write_fn=_write)


# ---------------------------------------------------------------------------
# remove_tags
# ---------------------------------------------------------------------------

def test_remove_tags_removes_specified():
    existing = {_TAGS_KEY: "alpha,beta,gamma"}
    read = _make_read({("proj", "dev"): existing})
    result = remove_tags("proj", "dev", ["beta"], read_fn=read, write_fn=_write)
    assert "beta" not in result.tags
    assert "alpha" in result.tags


def test_remove_tags_clears_key_when_empty():
    existing = {_TAGS_KEY: "only"}
    read = _make_read({("proj", "dev"): existing})
    remove_tags("proj", "dev", ["only"], read_fn=read, write_fn=_write)
    written = _read_written("proj", "dev")
    assert _TAGS_KEY not in written


def test_remove_tags_raises_on_empty_list():
    read = _make_read({("proj", "dev"): {}})
    with pytest.raises(TagError):
        remove_tags("proj", "dev", [], read_fn=read, write_fn=_write)


# ---------------------------------------------------------------------------
# list_tags
# ---------------------------------------------------------------------------

def test_list_tags_returns_sorted():
    existing = {_TAGS_KEY: "zebra,apple,mango"}
    read = _make_read({("proj", "dev"): existing})
    result = list_tags("proj", "dev", read_fn=read)
    assert result.tags == sorted(["zebra", "apple", "mango"])


def test_list_tags_empty_when_none_set():
    read = _make_read({("proj", "dev"): {"KEY": "value"}})
    result = list_tags("proj", "dev", read_fn=read)
    assert result.tags == []
