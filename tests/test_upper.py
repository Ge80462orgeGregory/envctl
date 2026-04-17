import pytest
from envctl.upper import upper_env, UpperError


def _make_read(data: dict):
    def _read(project, environment):
        return data.get((project, environment))
    return _read


_written = {}


def _write(project, environment, data):
    _written[(project, environment)] = dict(data)


def setup_function():
    _written.clear()


def test_upper_converts_all_values():
    read = _make_read({("myapp", "dev"): {"FOO": "hello", "BAR": "world"}})
    result = upper_env("myapp", "dev", read, _write)
    assert result.total_changed == 2
    assert _written[("myapp", "dev")] == {"FOO": "HELLO", "BAR": "WORLD"}


def test_upper_skips_already_uppercase():
    read = _make_read({("myapp", "dev"): {"FOO": "HELLO", "BAR": "world"}})
    result = upper_env("myapp", "dev", read, _write)
    assert result.total_changed == 1
    assert "BAR" in result.changed_keys
    assert "FOO" not in result.changed_keys


def test_upper_specific_keys_only():
    read = _make_read({("myapp", "dev"): {"FOO": "hello", "BAR": "world"}})
    result = upper_env("myapp", "dev", read, _write, keys=["FOO"])
    assert result.total_changed == 1
    assert _written[("myapp", "dev")]["FOO"] == "HELLO"
    assert _written[("myapp", "dev")]["BAR"] == "world"


def test_upper_dry_run_does_not_write():
    read = _make_read({("myapp", "dev"): {"FOO": "hello"}})
    result = upper_env("myapp", "dev", read, _write, dry_run=True)
    assert result.total_changed == 1
    assert ("myapp", "dev") not in _written


def test_upper_missing_environment_raises():
    read = _make_read({})
    with pytest.raises(UpperError):
        upper_env("myapp", "missing", read, _write)


def test_upper_empty_env_returns_zero_changed():
    read = _make_read({("myapp", "dev"): {}})
    result = upper_env("myapp", "dev", read, _write)
    assert result.total_changed == 0
    assert result.total_keys == 0


def test_upper_result_contains_project_and_environment():
    read = _make_read({("myapp", "prod"): {"KEY": "val"}})
    result = upper_env("myapp", "prod", read, _write)
    assert result.project == "myapp"
    assert result.environment == "prod"


def test_upper_to_dict_keys():
    read = _make_read({("myapp", "dev"): {"A": "b"}})
    result = upper_env("myapp", "dev", read, _write)
    d = result.to_dict()
    assert set(d.keys()) == {"project", "environment", "total_keys", "total_changed", "changed_keys"}
