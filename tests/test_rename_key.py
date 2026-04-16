import pytest
from envctl.rename_key import rename_key, RenameKeyError

_store: dict = {}


def _make_read(data: dict):
    def _read(project, environment):
        return dict(data.get((project, environment), {}))
    return _read


def _write(project, environment, data):
    _store[(project, environment)] = dict(data)


def setup_function():
    _store.clear()


def test_rename_key_success():
    read = _make_read({("app", "dev"): {"OLD_KEY": "value", "OTHER": "x"}})
    result = rename_key("app", "dev", "OLD_KEY", "NEW_KEY", read=read, write=_write)
    assert result.old_key == "OLD_KEY"
    assert result.new_key == "NEW_KEY"
    assert result.value == "value"
    assert _store[("app", "dev")]["NEW_KEY"] == "value"
    assert "OLD_KEY" not in _store[("app", "dev")]
    assert _store[("app", "dev")]["OTHER"] == "x"


def test_rename_key_preserves_order():
    read = _make_read({("app", "dev"): {"A": "1", "B": "2", "C": "3"}})
    rename_key("app", "dev", "B", "Z", read=read, write=_write)
    keys = list(_store[("app", "dev")].keys())
    assert keys == ["A", "Z", "C"]


def test_rename_key_missing_old_key_raises():
    read = _make_read({("app", "dev"): {"FOO": "bar"}})
    with pytest.raises(RenameKeyError, match="not found"):
        rename_key("app", "dev", "MISSING", "NEW", read=read, write=_write)


def test_rename_key_new_key_already_exists_raises():
    read = _make_read({("app", "dev"): {"FOO": "bar", "BAZ": "qux"}})
    with pytest.raises(RenameKeyError, match="already exists"):
        rename_key("app", "dev", "FOO", "BAZ", read=read, write=_write)


def test_rename_key_same_key_raises():
    read = _make_read({("app", "dev"): {"FOO": "bar"}})
    with pytest.raises(RenameKeyError, match="same"):
        rename_key("app", "dev", "FOO", "FOO", read=read, write=_write)


def test_rename_key_empty_old_key_raises():
    read = _make_read({("app", "dev"): {}})
    with pytest.raises(RenameKeyError, match="old_key"):
        rename_key("app", "dev", "", "NEW", read=read, write=_write)


def test_rename_key_empty_new_key_raises():
    read = _make_read({("app", "dev"): {"FOO": "bar"}})
    with pytest.raises(RenameKeyError, match="new_key"):
        rename_key("app", "dev", "FOO", "", read=read, write=_write)


def test_rename_key_to_dict():
    read = _make_read({("proj", "prod"): {"X": "42"}})
    result = rename_key("proj", "prod", "X", "Y", read=read, write=_write)
    d = result.to_dict()
    assert d["project"] == "proj"
    assert d["environment"] == "prod"
    assert d["old_key"] == "X"
    assert d["new_key"] == "Y"
    assert d["value"] == "42"
