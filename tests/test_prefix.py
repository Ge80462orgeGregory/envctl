import pytest
from envctl.prefix import add_prefix, strip_prefix, PrefixError

_store = {}


def _make_read(data: dict):
    def _read(project, environment):
        return dict(data)
    return _read


def _write(project, environment, data):
    _store[f"{project}/{environment}"] = dict(data)


def _read_written(project, environment):
    return _store.get(f"{project}/{environment}", {})


def setup_function():
    _store.clear()


def test_add_prefix_renames_keys():
    read = _make_read({"FOO": "1", "BAR": "2"})
    result = add_prefix("myapp", "dev", "APP_", read, _write)
    written = _read_written("myapp", "dev")
    assert "APP_FOO" in written
    assert "APP_BAR" in written
    assert "FOO" not in written
    assert result.total_changed == 2


def test_add_prefix_skips_already_prefixed():
    read = _make_read({"APP_FOO": "1", "BAR": "2"})
    result = add_prefix("myapp", "dev", "APP_", read, _write)
    assert "APP_FOO" in result.skipped
    assert result.total_changed == 1


def test_add_prefix_empty_prefix_raises():
    read = _make_read({"FOO": "1"})
    with pytest.raises(PrefixError):
        add_prefix("myapp", "dev", "", read, _write)


def test_add_prefix_empty_env_raises():
    read = _make_read({})
    with pytest.raises(PrefixError):
        add_prefix("myapp", "dev", "APP_", read, _write)


def test_strip_prefix_removes_prefix():
    read = _make_read({"APP_FOO": "1", "APP_BAR": "2"})
    result = strip_prefix("myapp", "dev", "APP_", read, _write)
    written = _read_written("myapp", "dev")
    assert "FOO" in written
    assert "BAR" in written
    assert "APP_FOO" not in written
    assert result.total_changed == 2


def test_strip_prefix_skips_non_matching():
    read = _make_read({"APP_FOO": "1", "OTHER": "2"})
    result = strip_prefix("myapp", "dev", "APP_", read, _write)
    assert "OTHER" in result.skipped
    assert result.total_changed == 1


def test_strip_prefix_empty_prefix_raises():
    read = _make_read({"FOO": "1"})
    with pytest.raises(PrefixError):
        strip_prefix("myapp", "dev", "", read, _write)


def test_strip_prefix_empty_env_raises():
    read = _make_read({})
    with pytest.raises(PrefixError):
        strip_prefix("myapp", "dev", "APP_", read, _write)


def test_result_to_dict_contains_expected_keys():
    read = _make_read({"FOO": "bar"})
    result = add_prefix("proj", "staging", "X_", read, _write)
    d = result.to_dict()
    assert "project" in d
    assert "environment" in d
    assert "changed" in d
    assert "skipped" in d
    assert "total_changed" in d
