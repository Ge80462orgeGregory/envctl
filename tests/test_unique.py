"""Tests for envctl.unique.find_unique."""
from __future__ import annotations
import pytest
from envctl.unique import find_unique, UniqueError


def _make_read(store: dict):
    def _read(project: str, env: str) -> dict:
        return store.get((project, env), {})
    return _read


def _make_list(envs):
    def _list(project: str):
        return envs
    return _list


STORE = {
    ("myapp", "local"): {"DB_HOST": "localhost", "DEBUG": "true", "LOCAL_ONLY": "yes"},
    ("myapp", "staging"): {"DB_HOST": "staging.db", "DEBUG": "false"},
    ("myapp", "prod"): {"DB_HOST": "prod.db", "SECRET": "abc"},
}

_read = _make_read(STORE)
_list = _make_list(["local", "staging", "prod"])


def test_unique_keys_not_in_others():
    result = find_unique("myapp", "local", ["staging", "prod"], _read)
    assert "LOCAL_ONLY" in result.unique_keys
    assert result.unique_keys["LOCAL_ONLY"] == "yes"


def test_shared_keys_excluded():
    result = find_unique("myapp", "local", ["staging", "prod"], _read)
    assert "DB_HOST" not in result.unique_keys
    assert "DEBUG" not in result.unique_keys


def test_total_unique_count():
    result = find_unique("myapp", "local", ["staging", "prod"], _read)
    assert result.total_unique == 1


def test_result_metadata():
    result = find_unique("myapp", "local", ["staging"], _read)
    assert result.project == "myapp"
    assert result.source_env == "local"
    assert result.compared_envs == ["staging"]


def test_unique_with_no_compared_envs_uses_list_fn():
    result = find_unique("myapp", "prod", [], _read, list_envs_fn=_list)
    # SECRET is only in prod
    assert "SECRET" in result.unique_keys
    assert "local" in result.compared_envs
    assert "staging" in result.compared_envs
    assert "prod" not in result.compared_envs


def test_empty_project_raises():
    with pytest.raises(UniqueError, match="project"):
        find_unique("", "local", ["staging"], _read)


def test_empty_source_env_raises():
    with pytest.raises(UniqueError, match="source_env"):
        find_unique("myapp", "", ["staging"], _read)


def test_missing_source_env_raises():
    r = _make_read({})
    with pytest.raises(UniqueError, match="empty or missing"):
        find_unique("myapp", "ghost", ["staging"], r)


def test_no_compared_envs_and_no_list_fn_raises():
    with pytest.raises(UniqueError, match="list_envs_fn"):
        find_unique("myapp", "local", [], _read)


def test_to_dict_shape():
    result = find_unique("myapp", "local", ["staging", "prod"], _read)
    d = result.to_dict()
    assert "project" in d
    assert "source_env" in d
    assert "compared_envs" in d
    assert "unique_keys" in d
    assert "total_unique" in d
    assert d["total_unique"] == result.total_unique
