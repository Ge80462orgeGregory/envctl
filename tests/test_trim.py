"""Tests for envctl.trim."""

from __future__ import annotations

import pytest

from envctl.trim import TrimError, TrimResult, trim_env

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

_store: dict[tuple[str, str], dict[str, str]] = {}


def _make_read(data: dict[tuple[str, str], dict[str, str]]):
    def _read(project: str, env: str) -> dict[str, str]:
        return dict(data.get((project, env), {}))
    return _read


def _write(project: str, env: str, variables: dict[str, str]) -> None:
    _store[(project, env)] = dict(variables)


def _read_written(project: str, env: str) -> dict[str, str]:
    return dict(_store.get((project, env), {}))


def setup_function():
    _store.clear()


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------

def test_trim_removes_empty_keys_by_default():
    data = {("myapp", "staging"): {"A": "hello", "B": "", "C": ""}}
    result = trim_env("myapp", "staging", read_env=_make_read(data), write_env=_write)
    assert result.removed == ["B", "C"] or set(result.removed) == {"B", "C"}
    assert "A" in result.kept
    assert _read_written("myapp", "staging") == {"A": "hello"}


def test_trim_specific_keys():
    data = {("myapp", "prod"): {"X": "1", "Y": "2", "Z": "3"}}
    result = trim_env(
        "myapp", "prod",
        keys=["X", "Z"],
        read_env=_make_read(data),
        write_env=_write,
    )
    assert set(result.removed) == {"X", "Z"}
    assert result.kept == ["Y"]
    assert _read_written("myapp", "prod") == {"Y": "2"}


def test_trim_dry_run_does_not_write():
    data = {("myapp", "local"): {"A": "", "B": "keep"}}
    result = trim_env(
        "myapp", "local",
        dry_run=True,
        read_env=_make_read(data),
        write_env=_write,
    )
    assert "A" in result.removed
    assert _store == {}  # nothing written


def test_trim_raises_on_missing_env():
    with pytest.raises(TrimError, match="does not exist or is empty"):
        trim_env("ghost", "dev", read_env=_make_read({}), write_env=_write)


def test_trim_raises_on_unknown_keys():
    data = {("myapp", "dev"): {"A": "1"}}
    with pytest.raises(TrimError, match="Keys not found"):
        trim_env(
            "myapp", "dev",
            keys=["NOPE"],
            read_env=_make_read(data),
            write_env=_write,
        )


def test_trim_result_total_removed():
    data = {("myapp", "staging"): {"A": "", "B": "", "C": "val"}}
    result = trim_env("myapp", "staging", read_env=_make_read(data), write_env=_write)
    assert result.total_removed == 2


def test_trim_no_empty_keys_writes_nothing():
    data = {("myapp", "prod"): {"A": "1", "B": "2"}}
    result = trim_env("myapp", "prod", read_env=_make_read(data), write_env=_write)
    assert result.removed == []
    assert _store == {}  # no write triggered
