import pytest
from envctl.squash import squash_envs, SquashError, SquashResult

_store: dict = {}


def _make_read(data: dict):
    def _read(project, env):
        return data.get((project, env), {})
    return _read


_written = {}


def _write(project, env, data):
    _written[(project, env)] = dict(data)


def setup_function():
    _written.clear()


def test_squash_merges_unique_keys():
    read = _make_read({
        ("proj", "dev"): {"A": "1", "B": "2"},
        ("proj", "qa"): {"C": "3"},
    })
    result = squash_envs("proj", ["dev", "qa"], "merged", read, _write)
    assert result.merged == {"A": "1", "B": "2", "C": "3"}
    assert result.total_conflicts == 0
    assert _written[("proj", "merged")] == {"A": "1", "B": "2", "C": "3"}


def test_squash_detects_conflicts():
    read = _make_read({
        ("proj", "dev"): {"A": "1"},
        ("proj", "qa"): {"A": "99"},
    })
    result = squash_envs("proj", ["dev", "qa"], "merged", read, _write, overwrite=False)
    assert "A" in result.conflicts
    assert result.merged["A"] == "1"  # first-write wins


def test_squash_overwrite_uses_last_value():
    read = _make_read({
        ("proj", "dev"): {"A": "1"},
        ("proj", "qa"): {"A": "99"},
    })
    result = squash_envs("proj", ["dev", "qa"], "merged", read, _write, overwrite=True)
    assert result.merged["A"] == "99"


def test_squash_raises_on_empty_sources():
    read = _make_read({})
    with pytest.raises(SquashError, match="At least one source"):
        squash_envs("proj", [], "merged", read, _write)


def test_squash_raises_when_target_in_sources():
    read = _make_read({("proj", "dev"): {"A": "1"}})
    with pytest.raises(SquashError, match="cannot be one of the sources"):
        squash_envs("proj", ["dev", "merged"], "merged", read, _write)


def test_squash_result_to_dict():
    read = _make_read({
        ("proj", "dev"): {"X": "1"},
    })
    result = squash_envs("proj", ["dev"], "out", read, _write)
    d = result.to_dict()
    assert d["project"] == "proj"
    assert d["target"] == "out"
    assert d["total_keys"] == 1
    assert d["total_conflicts"] == 0


def test_squash_identical_values_not_flagged_as_conflict():
    read = _make_read({
        ("proj", "dev"): {"A": "same"},
        ("proj", "qa"): {"A": "same"},
    })
    result = squash_envs("proj", ["dev", "qa"], "merged", read, _write)
    assert result.total_conflicts == 0
