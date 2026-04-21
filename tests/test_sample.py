"""Tests for envctl.sample."""

from __future__ import annotations

import pytest

from envctl.sample import SampleError, SampleResult, sample_env

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
    return _store.get((project, environment), {})


def setup_function():
    _store.clear()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_sample_writes_placeholder_values():
    result = sample_env(
        "myapp", "local", ["DB_HOST", "DB_PORT"],
        read_env=_make_read({}),
        write_env=_write,
    )
    written = _read_written("myapp", "local")
    assert written["DB_HOST"] == "CHANGEME"
    assert written["DB_PORT"] == "CHANGEME"
    assert result.total_generated() == 2
    assert result.skipped == []


def test_sample_skips_existing_keys_without_overwrite():
    existing = {"DB_HOST": "localhost"}
    result = sample_env(
        "myapp", "local", ["DB_HOST", "DB_PORT"],
        read_env=_make_read({("myapp", "local"): existing}),
        write_env=_write,
    )
    assert "DB_HOST" in result.skipped
    assert "DB_PORT" in result.keys
    written = _read_written("myapp", "local")
    assert written["DB_HOST"] == "localhost"
    assert written["DB_PORT"] == "CHANGEME"


def test_sample_overwrites_existing_keys_when_flag_set():
    existing = {"DB_HOST": "localhost"}
    result = sample_env(
        "myapp", "local", ["DB_HOST"],
        overwrite=True,
        read_env=_make_read({("myapp", "local"): existing}),
        write_env=_write,
    )
    assert result.skipped == []
    assert "DB_HOST" in result.keys
    assert _read_written("myapp", "local")["DB_HOST"] == "CHANGEME"


def test_sample_custom_placeholder():
    result = sample_env(
        "myapp", "prod", ["SECRET_KEY"],
        placeholder="<REPLACE_ME>",
        read_env=_make_read({}),
        write_env=_write,
    )
    assert _read_written("myapp", "prod")["SECRET_KEY"] == "<REPLACE_ME>"


def test_sample_raises_on_empty_keys():
    with pytest.raises(SampleError):
        sample_env(
            "myapp", "local", [],
            read_env=_make_read({}),
            write_env=_write,
        )


def test_sample_result_to_dict():
    result = SampleResult(project="p", environment="e", keys=["A", "B"], skipped=["C"])
    d = result.to_dict()
    assert d["total_generated"] == 2
    assert d["skipped"] == ["C"]
    assert d["project"] == "p"
