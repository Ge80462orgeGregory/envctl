import pytest
from envctl.truncate import truncate_env, TruncateError

_store = {}


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


def test_truncate_shortens_long_values():
    read = _make_read({("proj", "dev"): {"KEY": "hello_world"}})
    result = truncate_env("proj", "dev", max_length=5, read_env=read, write_env=_write)
    assert result.total_truncated == 1
    assert result.changes["KEY"] == "hello"
    assert _read_written("proj", "dev")["KEY"] == "hello"


def test_truncate_skips_short_values():
    read = _make_read({("proj", "dev"): {"KEY": "hi"}})
    result = truncate_env("proj", "dev", max_length=10, read_env=read, write_env=_write)
    assert result.total_truncated == 0
    assert result.changes == {}


def test_truncate_specific_keys_only():
    data = {"A": "long_value", "B": "another_long_value"}
    read = _make_read({("proj", "dev"): data})
    result = truncate_env("proj", "dev", max_length=4, keys=["A"], read_env=read, write_env=_write)
    assert "A" in result.changes
    assert "B" not in result.changes
    written = _read_written("proj", "dev")
    assert written["A"] == "long"
    assert written["B"] == "another_long_value"


def test_truncate_invalid_max_length_raises():
    read = _make_read({("proj", "dev"): {"KEY": "value"}})
    with pytest.raises(TruncateError, match="max_length must be at least 1"):
        truncate_env("proj", "dev", max_length=0, read_env=read, write_env=_write)


def test_truncate_empty_env_raises():
    read = _make_read({})
    with pytest.raises(TruncateError):
        truncate_env("proj", "dev", max_length=5, read_env=read, write_env=_write)


def test_truncate_missing_key_in_keys_list_ignored():
    read = _make_read({("proj", "dev"): {"A": "hello"}})
    result = truncate_env("proj", "dev", max_length=3, keys=["A", "MISSING"], read_env=read, write_env=_write)
    assert "MISSING" not in result.changes
    assert result.changes["A"] == "hel"


def test_truncate_result_to_dict():
    read = _make_read({("proj", "dev"): {"X": "abcdef"}})
    result = truncate_env("proj", "dev", max_length=3, read_env=read, write_env=_write)
    d = result.to_dict()
    assert d["project"] == "proj"
    assert d["environment"] == "dev"
    assert d["total_truncated"] == 1
    assert d["changes"]["X"] == "abc"
