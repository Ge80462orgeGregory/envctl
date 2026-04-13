"""Tests for envctl.clone module."""

import pytest

from envctl.clone import CloneError, CloneResult, clone_project


def _make_read(data: dict):
    """Return a fake read_env that looks up (project, env)."""
    def _read(project, env, **kwargs):
        return data.get((project, env), {})
    return _read


_written: dict = {}


def _write(project, env, variables, **kwargs):
    _written[(project, env)] = dict(variables)


def _make_list(data: dict):
    """Return a fake list_environments that looks up project."""
    def _list(project, **kwargs):
        return data.get(project, [])
    return _list


@pytest.fixture(autouse=True)
def clear_written():
    _written.clear()


def test_clone_copies_all_envs():
    source_data = {
        ("alpha", "local"): {"A": "1"},
        ("alpha", "staging"): {"A": "2"},
    }
    list_fn = _make_list({"alpha": ["local", "staging"], "beta": []})
    read_fn = _make_read(source_data)

    result = clone_project(
        "alpha", "beta",
        _list_environments=list_fn,
        _read_env=read_fn,
        _write_env=_write,
    )

    assert result.total_cloned == 2
    assert "local" in result.cloned_envs
    assert "staging" in result.cloned_envs
    assert _written[("beta", "local")] == {"A": "1"}
    assert _written[("beta", "staging")] == {"A": "2"}


def test_clone_skips_existing_without_overwrite():
    source_data = {("alpha", "local"): {"X": "1"}, ("alpha", "prod"): {"Y": "2"}}
    list_fn = _make_list({"alpha": ["local", "prod"], "beta": ["local"]})
    read_fn = _make_read(source_data)

    result = clone_project(
        "alpha", "beta",
        overwrite=False,
        _list_environments=list_fn,
        _read_env=read_fn,
        _write_env=_write,
    )

    assert result.total_cloned == 1
    assert "prod" in result.cloned_envs
    assert "local" in result.skipped_envs
    assert ("beta", "local") not in _written


def test_clone_overwrites_existing_when_flag_set():
    source_data = {("alpha", "local"): {"X": "new"}}
    list_fn = _make_list({"alpha": ["local"], "beta": ["local"]})
    read_fn = _make_read(source_data)

    result = clone_project(
        "alpha", "beta",
        overwrite=True,
        _list_environments=list_fn,
        _read_env=read_fn,
        _write_env=_write,
    )

    assert result.total_cloned == 1
    assert result.skipped_envs == []
    assert _written[("beta", "local")] == {"X": "new"}


def test_clone_raises_when_same_project():
    with pytest.raises(CloneError, match="must differ"):
        clone_project("alpha", "alpha")


def test_clone_raises_when_source_has_no_envs():
    list_fn = _make_list({"alpha": []})
    with pytest.raises(CloneError, match="No environments found"):
        clone_project(
            "alpha", "beta",
            _list_environments=list_fn,
            _read_env=_make_read({}),
            _write_env=_write,
        )


def test_clone_result_dataclass_defaults():
    r = CloneResult(source_project="a", dest_project="b")
    assert r.cloned_envs == []
    assert r.skipped_envs == []
    assert r.total_cloned == 0
