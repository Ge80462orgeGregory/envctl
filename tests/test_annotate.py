"""Tests for envctl.annotate."""

from __future__ import annotations

import pytest

from envctl.annotate import AnnotateError, annotate_env, _get_annotations


def _make_read(store: dict):
    def _read(project: str, environment: str) -> dict[str, str]:
        return dict(store.get((project, environment), {}))
    return _read


def _make_write(store: dict):
    def _write(project: str, environment: str, data: dict[str, str]) -> None:
        store[(project, environment)] = dict(data)
    return _write


def _setup():
    store = {
        ("myapp", "dev"): {"DB_HOST": "localhost", "API_KEY": "abc123"},
    }
    return store, _make_read(store), _make_write(store)


def test_annotate_adds_new_description():
    store, read, write = _setup()
    result = annotate_env(read, write, "myapp", "dev", {"DB_HOST": "Database hostname"})
    assert "DB_HOST" in result.added
    assert result.added["DB_HOST"] == "Database hostname"
    assert result.total_changes == 1


def test_annotate_updates_existing_description():
    store, read, write = _setup()
    annotate_env(read, write, "myapp", "dev", {"DB_HOST": "Old desc"})
    result = annotate_env(read, write, "myapp", "dev", {"DB_HOST": "New desc"})
    assert "DB_HOST" in result.updated
    assert result.total_changes == 1


def test_annotate_no_change_when_description_identical():
    store, read, write = _setup()
    annotate_env(read, write, "myapp", "dev", {"DB_HOST": "Same desc"})
    result = annotate_env(read, write, "myapp", "dev", {"DB_HOST": "Same desc"})
    assert result.total_changes == 0


def test_annotate_removes_description():
    store, read, write = _setup()
    annotate_env(read, write, "myapp", "dev", {"DB_HOST": "To remove"})
    result = annotate_env(read, write, "myapp", "dev", {}, remove_keys=["DB_HOST"])
    assert "DB_HOST" in result.removed
    assert result.total_changes == 1


def test_annotate_remove_nonexistent_key_is_noop():
    store, read, write = _setup()
    result = annotate_env(read, write, "myapp", "dev", {"API_KEY": "desc"}, remove_keys=["MISSING"])
    assert "MISSING" not in result.removed


def test_annotate_raises_for_unknown_key():
    store, read, write = _setup()
    with pytest.raises(AnnotateError, match="UNKNOWN_KEY"):
        annotate_env(read, write, "myapp", "dev", {"UNKNOWN_KEY": "desc"})


def test_annotate_multiple_keys():
    store, read, write = _setup()
    result = annotate_env(
        read, write, "myapp", "dev",
        {"DB_HOST": "Database host", "API_KEY": "API secret key"},
    )
    assert len(result.added) == 2
    assert result.total_changes == 2


def test_get_annotations_returns_stored_descriptions():
    store, read, write = _setup()
    annotate_env(read, write, "myapp", "dev", {"DB_HOST": "Host", "API_KEY": "Key"})
    annotations = _get_annotations(read, "myapp", "dev")
    assert annotations["DB_HOST"] == "Host"
    assert annotations["API_KEY"] == "Key"


def test_annotate_result_to_dict():
    store, read, write = _setup()
    result = annotate_env(read, write, "myapp", "dev", {"DB_HOST": "Host"})
    d = result.to_dict()
    assert d["project"] == "myapp"
    assert d["environment"] == "dev"
    assert "added" in d
    assert "updated" in d
    assert "removed" in d
    assert "total_changes" in d


def test_annotate_raises_when_env_empty_and_no_descriptions():
    store = {("empty", "dev"): {}}
    read = _make_read(store)
    write = _make_write(store)
    with pytest.raises(AnnotateError):
        annotate_env(read, write, "empty", "dev", {})
