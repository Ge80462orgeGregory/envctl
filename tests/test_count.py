import pytest
from envctl.count import count_env, CountError, CountResult


def _make_read(data: dict[str, dict[str, dict[str, str]]]):
    def _read(project: str, environment: str) -> dict[str, str]:
        return data.get(project, {}).get(environment, {})
    return _read


def test_count_returns_correct_totals():
    read = _make_read({"app": {"dev": {"A": "1", "B": "2", "C": ""}}})
    result = count_env("app", "dev", read)
    assert result.total == 3
    assert result.non_empty == 2
    assert result.empty == 1


def test_count_all_empty_values():
    read = _make_read({"app": {"dev": {"X": "", "Y": "  "}}})
    result = count_env("app", "dev", read)
    assert result.total == 2
    assert result.non_empty == 0
    assert result.empty == 2


def test_count_all_non_empty_values():
    read = _make_read({"app": {"prod": {"KEY": "val"}}})
    result = count_env("app", "prod", read)
    assert result.total == 1
    assert result.non_empty == 1
    assert result.empty == 0


def test_count_empty_env():
    read = _make_read({"app": {"staging": {}}})
    result = count_env("app", "staging", read)
    assert result.total == 0
    assert result.non_empty == 0
    assert result.empty == 0


def test_count_result_project_and_environment():
    read = _make_read({"myapp": {"test": {"K": "v"}}})
    result = count_env("myapp", "test", read)
    assert result.project == "myapp"
    assert result.environment == "test"


def test_count_raises_on_empty_project():
    read = _make_read({})
    with pytest.raises(CountError, match="project"):
        count_env("", "dev", read)


def test_count_raises_on_empty_environment():
    read = _make_read({})
    with pytest.raises(CountError, match="environment"):
        count_env("app", "", read)


def test_count_to_dict():
    read = _make_read({"p": {"e": {"A": "1", "B": ""}}})
    result = count_env("p", "e", read)
    d = result.to_dict()
    assert d["total"] == 2
    assert d["non_empty"] == 1
    assert d["empty"] == 1
    assert d["project"] == "p"
    assert d["environment"] == "e"
