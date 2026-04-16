import pytest
from envctl.filter import filter_env, FilterError, FilterResult


def _make_read(data: dict):
    def _read(project, environment):
        return data.get((project, environment), {})
    return _read


ENV_DATA = {
    ("myapp", "staging"): {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "APP_SECRET": "abc123",
        "APP_DEBUG": "true",
        "CACHE_URL": "redis://localhost",
    }
}

_read = _make_read(ENV_DATA)


def test_filter_by_prefix():
    result = filter_env("myapp", "staging", _read, prefix="DB_")
    assert set(result.matched.keys()) == {"DB_HOST", "DB_PORT"}


def test_filter_by_suffix():
    result = filter_env("myapp", "staging", _read, suffix="_URL")
    assert set(result.matched.keys()) == {"CACHE_URL"}


def test_filter_by_contains():
    result = filter_env("myapp", "staging", _read, contains="APP")
    assert set(result.matched.keys()) == {"APP_SECRET", "APP_DEBUG"}


def test_filter_by_value_contains():
    result = filter_env("myapp", "staging", _read, value_contains="localhost")
    assert set(result.matched.keys()) == {"DB_HOST", "CACHE_URL"}


def test_filter_invert():
    result = filter_env("myapp", "staging", _read, prefix="DB_", invert=True)
    assert "DB_HOST" not in result.matched
    assert "DB_PORT" not in result.matched
    assert "APP_SECRET" in result.matched


def test_filter_combined_prefix_and_value():
    result = filter_env("myapp", "staging", _read, prefix="APP_", value_contains="true")
    assert set(result.matched.keys()) == {"APP_DEBUG"}


def test_filter_no_match_returns_empty():
    result = filter_env("myapp", "staging", _read, prefix="NONEXISTENT_")
    assert result.matched == {}
    assert result.total_scanned == 5


def test_filter_total_scanned():
    result = filter_env("myapp", "staging", _read)
    assert result.total_scanned == 5
    assert result.total_matched() == 5


def test_filter_empty_project_raises():
    with pytest.raises(FilterError, match="Project"):
        filter_env("", "staging", _read)


def test_filter_empty_environment_raises():
    with pytest.raises(FilterError, match="Environment"):
        filter_env("myapp", "", _read)


def test_filter_to_dict():
    result = filter_env("myapp", "staging", _read, prefix="DB_")
    d = result.to_dict()
    assert d["project"] == "myapp"
    assert d["environment"] == "staging"
    assert d["total_matched"] == 2
    assert d["total_scanned"] == 5
    assert "DB_HOST" in d["matched"]
