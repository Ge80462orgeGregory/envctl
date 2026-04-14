"""Tests for envctl.scaffold."""

from __future__ import annotations

import pytest

from envctl.scaffold import (
    DEFAULT_ENVIRONMENTS,
    DEFAULT_KEYS,
    ScaffoldError,
    ScaffoldResult,
    scaffold_project,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_written: dict[tuple[str, str], dict[str, str]] = {}
_existing: dict[str, list[str]] = {}


def setup_function():
    _written.clear()
    _existing.clear()


def _write(project: str, env: str, variables: dict[str, str]) -> None:
    _written[(project, env)] = dict(variables)


def _list(project: str) -> list[str]:
    return list(_existing.get(project, []))


def _scaffold(**kwargs) -> ScaffoldResult:
    return scaffold_project(**kwargs, _write_env=_write, _list_environments=_list)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_scaffold_creates_default_environments():
    result = _scaffold(project="myapp")
    assert sorted(result.environments_created) == sorted(DEFAULT_ENVIRONMENTS)
    assert result.skipped_environments == []


def test_scaffold_writes_default_keys_to_each_env():
    _scaffold(project="myapp")
    for env in DEFAULT_ENVIRONMENTS:
        assert ("myapp", env) in _written
        assert _written[("myapp", env)] == DEFAULT_KEYS


def test_scaffold_keys_written_count():
    result = _scaffold(project="myapp")
    assert result.keys_written == len(DEFAULT_KEYS) * len(DEFAULT_ENVIRONMENTS)


def test_scaffold_custom_environments():
    result = _scaffold(project="myapp", environments=["dev", "prod"])
    assert sorted(result.environments_created) == ["dev", "prod"]


def test_scaffold_extra_keys_merged():
    _scaffold(project="myapp", extra_keys={"REDIS_URL": ""})
    env_vars = _written[("myapp", "local")]
    assert "REDIS_URL" in env_vars
    assert "APP_ENV" in env_vars


def test_scaffold_skips_existing_env_without_overwrite():
    _existing["myapp"] = ["local"]
    result = _scaffold(project="myapp")
    assert "local" in result.skipped_environments
    assert "local" not in result.environments_created
    assert ("myapp", "local") not in _written


def test_scaffold_overwrites_existing_env_when_flag_set():
    _existing["myapp"] = ["local"]
    result = _scaffold(project="myapp", overwrite=True)
    assert "local" not in result.skipped_environments
    assert "local" in result.environments_created
    assert ("myapp", "local") in _written


def test_scaffold_raises_on_empty_project_name():
    with pytest.raises(ScaffoldError, match="Project name"):
        _scaffold(project="")


def test_scaffold_raises_on_whitespace_project_name():
    with pytest.raises(ScaffoldError, match="Project name"):
        _scaffold(project="   ")


def test_scaffold_raises_on_empty_environments_list():
    with pytest.raises(ScaffoldError, match="At least one environment"):
        _scaffold(project="myapp", environments=[])


def test_scaffold_result_project_name():
    result = _scaffold(project="alpha")
    assert result.project == "alpha"
