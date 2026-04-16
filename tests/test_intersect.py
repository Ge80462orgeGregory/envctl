"""Tests for envctl.intersect"""
import pytest
from envctl.intersect import intersect_envs, IntersectError, IntersectResult


def _make_read(stores):
    def _read(project, env):
        return stores.get((project, env), {})
    return _read


SRC = {"A": "1", "B": "2", "C": "3"}
TGT = {"B": "2", "C": "99", "D": "4"}


@pytest.fixture
def _read():
    return _make_read({("proj", "dev"): SRC, ("proj", "prod"): TGT})


def test_common_keys_returned(_read):
    result = intersect_envs("proj", "dev", "prod", _read)
    assert result.common_keys == ["B", "C"]


def test_same_value_keys(_read):
    result = intersect_envs("proj", "dev", "prod", _read)
    assert result.common_with_same_value == ["B"]


def test_diff_value_keys(_read):
    result = intersect_envs("proj", "dev", "prod", _read)
    assert result.common_with_diff_value == ["C"]


def test_total_equals_common_key_count(_read):
    result = intersect_envs("proj", "dev", "prod", _read)
    assert result.total == 2


def test_no_common_keys():
    read = _make_read({("p", "a"): {"X": "1"}, ("p", "b"): {"Y": "2"}})
    result = intersect_envs("p", "a", "b", read)
    assert result.common_keys == []
    assert result.total == 0


def test_missing_source_raises():
    read = _make_read({("p", "prod"): {"A": "1"}})
    with pytest.raises(IntersectError, match="dev"):
        intersect_envs("p", "dev", "prod", read)


def test_missing_target_raises():
    read = _make_read({("p", "dev"): {"A": "1"}})
    with pytest.raises(IntersectError, match="prod"):
        intersect_envs("p", "dev", "prod", read)


def test_to_dict_keys(_read):
    result = intersect_envs("proj", "dev", "prod", _read)
    d = result.to_dict()
    assert d["project"] == "proj"
    assert d["source_env"] == "dev"
    assert d["target_env"] == "prod"
    assert "common_keys" in d
    assert "total" in d


def test_result_type(_read):
    result = intersect_envs("proj", "dev", "prod", _read)
    assert isinstance(result, IntersectResult)
