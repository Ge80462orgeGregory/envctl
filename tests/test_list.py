"""Unit tests for envctl/list_.py."""

import pytest

from envctl.list_ import list_all, list_project_envs, format_list, ListError, ListResult


def _make_store(projects_envs: dict):
    """Return patched list_projects / list_environments callables."""
    def _list_projects(envs_dir):
        return list(projects_envs.keys())

    def _list_environments(envs_dir, project):
        return projects_envs.get(project, [])

    return _list_projects, _list_environments


@pytest.fixture()
def patch_store(monkeypatch):
    def _apply(data):
        lp, le = _make_store(data)
        monkeypatch.setattr("envctl.list_.list_projects", lp)
        monkeypatch.setattr("envctl.list_.list_environments", le)
    return _apply


def test_list_all_returns_sorted_projects(patch_store):
    patch_store({"beta": ["staging"], "alpha": ["local", "prod"]})
    results = list_all("/fake")
    assert [r.project for r in results] == ["alpha", "beta"]


def test_list_all_returns_sorted_envs(patch_store):
    patch_store({"myapp": ["prod", "local", "staging"]})
    results = list_all("/fake")
    assert results[0].entries == ["local", "prod", "staging"]


def test_list_all_empty(patch_store):
    patch_store({})
    results = list_all("/fake")
    assert results == []


def test_list_project_envs_known(patch_store):
    patch_store({"myapp": ["local", "prod"]})
    result = list_project_envs("/fake", "myapp")
    assert result.project == "myapp"
    assert result.entries == ["local", "prod"]


def test_list_project_envs_unknown_raises(patch_store):
    patch_store({"myapp": ["local"]})
    with pytest.raises(ListError, match="not found"):
        list_project_envs("/fake", "ghost")


def test_format_list_empty():
    assert format_list([]) == "No projects found."


def test_format_list_single_project():
    results = [ListResult(project="myapp", entries=["local", "prod"])]
    output = format_list(results)
    assert "[myapp]" in output
    assert "- local" in output
    assert "- prod" in output


def test_format_list_no_envs():
    results = [ListResult(project="empty", entries=[])]
    output = format_list(results)
    assert "(no environments)" in output


def test_format_list_multiple_projects():
    results = [
        ListResult(project="alpha", entries=["local"]),
        ListResult(project="beta", entries=["staging"]),
    ]
    output = format_list(results)
    assert output.index("[alpha]") < output.index("[beta]")
