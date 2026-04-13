"""Tests for envctl.search."""

import pytest
from envctl.search import SearchError, SearchMatch, SearchResult, format_search, search_envs


def _make_read(data: dict):
    """Return a read_fn that looks up (project, env) in data."""
    def _read(project, env):
        return data.get((project, env), {})
    return _read


_PROJECTS = ["alpha", "beta"]
_ENVS = {"alpha": ["local", "prod"], "beta": ["local"]}


def _list_projects():
    return _PROJECTS


def _list_environments(project):
    return _ENVS.get(project, [])


_DATA = {
    ("alpha", "local"): {"DB_HOST": "localhost", "SECRET": "abc123"},
    ("alpha", "prod"): {"DB_HOST": "prod.db.example.com", "SECRET": "xyz789"},
    ("beta", "local"): {"API_KEY": "key-abc", "TIMEOUT": "30"},
}


def _search(**kwargs):
    return search_envs(
        read_fn=_make_read(_DATA),
        list_projects_fn=_list_projects,
        list_environments_fn=_list_environments,
        **kwargs,
    )


def test_search_finds_key_match():
    result = _search(query="DB_HOST")
    assert result.total == 2
    keys = {m.key for m in result.matches}
    assert keys == {"DB_HOST"}


def test_search_finds_value_match():
    result = _search(query="abc")
    # SECRET=abc123 in alpha/local and API_KEY=key-abc in beta/local
    assert result.total == 2


def test_search_keys_only():
    result = _search(query="key", search_keys=True, search_values=False)
    assert all("key" in m.key.lower() for m in result.matches)


def test_search_values_only():
    result = _search(query="localhost", search_keys=False, search_values=True)
    assert result.total == 1
    assert result.matches[0].environment == "local"


def test_search_case_sensitive_no_match():
    result = _search(query="db_host", case_sensitive=True)
    assert result.total == 0


def test_search_case_sensitive_match():
    result = _search(query="DB_HOST", case_sensitive=True)
    assert result.total == 2


def test_search_scoped_to_project():
    result = _search(query="local", project="alpha")
    assert all(m.project == "alpha" for m in result.matches)


def test_search_empty_query_raises():
    with pytest.raises(SearchError, match="empty"):
        _search(query="")


def test_search_no_target_raises():
    with pytest.raises(SearchError, match="At least one"):
        _search(query="x", search_keys=False, search_values=False)


def test_search_no_matches():
    result = _search(query="DOES_NOT_EXIST_ANYWHERE")
    assert result.total == 0


def test_format_search_no_matches():
    result = SearchResult()
    assert format_search(result) == "No matches found."


def test_format_search_hides_values():
    result = SearchResult(
        matches=[SearchMatch(project="p", environment="e", key="FOO", value="bar")]
    )
    output = format_search(result, show_values=False)
    assert "bar" not in output
    assert "FOO" in output


def test_format_search_shows_count():
    result = SearchResult(
        matches=[SearchMatch(project="p", environment="e", key="X", value="y")]
    )
    output = format_search(result)
    assert "1 match" in output
