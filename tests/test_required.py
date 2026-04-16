import pytest
from envctl.required import check_required, RequiredError, RequiredResult


def _make_read(data: dict):
    def _read(project, environment):
        return data.get((project, environment))
    return _read


def _read(data):
    return _make_read(data)


def test_all_keys_present():
    r = _read({("proj", "dev"): {"A": "1", "B": "2"}})
    result = check_required("proj", "dev", ["A", "B"], r)
    assert result.satisfied
    assert result.missing == []
    assert set(result.present) == {"A", "B"}


def test_missing_key_detected():
    r = _read({("proj", "dev"): {"A": "1"}})
    result = check_required("proj", "dev", ["A", "B"], r)
    assert not result.satisfied
    assert "B" in result.missing
    assert "A" in result.present


def test_empty_value_counts_as_missing():
    r = _read({("proj", "dev"): {"A": "", "B": "val"}})
    result = check_required("proj", "dev", ["A", "B"], r)
    assert not result.satisfied
    assert "A" in result.missing


def test_no_required_keys_raises():
    r = _read({("proj", "dev"): {"A": "1"}})
    with pytest.raises(RequiredError):
        check_required("proj", "dev", [], r)


def test_missing_environment_raises():
    r = _read({})
    with pytest.raises(RequiredError, match="not found"):
        check_required("proj", "dev", ["A"], r)


def test_to_dict_contains_satisfied():
    r = _read({("proj", "dev"): {"A": "1"}})
    result = check_required("proj", "dev", ["A"], r)
    d = result.to_dict()
    assert d["satisfied"] is True
    assert d["project"] == "proj"
    assert d["environment"] == "dev"


def test_partial_match():
    r = _read({("proj", "prod"): {"X": "a", "Y": "b", "Z": ""}})
    result = check_required("proj", "prod", ["X", "Y", "Z"], r)
    assert not result.satisfied
    assert result.missing == ["Z"]
    assert set(result.present) == {"X", "Y"}
