import pytest
from envctl.typecheck import typecheck_env, infer_type, TypeCheckError


def _make_read(data: dict):
    def _read(project, environment):
        return data.get((project, environment))
    return _read


def test_infer_int():
    assert infer_type("42") == "int"


def test_infer_negative_int():
    assert infer_type("-5") == "int"


def test_infer_float():
    assert infer_type("3.14") == "float"


def test_infer_bool():
    assert infer_type("true") == "bool"
    assert infer_type("false") == "bool"
    assert infer_type("yes") == "bool"


def test_infer_url():
    assert infer_type("https://example.com") == "url"


def test_infer_email():
    assert infer_type("user@example.com") == "email"


def test_infer_string_fallback():
    assert infer_type("hello world") == "string"


def test_typecheck_passes_when_types_match():
    read = _make_read({("myapp", "prod"): {"PORT": "8080", "DEBUG": "false"}})
    result = typecheck_env("myapp", "prod", {"PORT": "int", "DEBUG": "bool"}, read)
    assert result.passed
    assert result.checked == 2
    assert result.issues == []


def test_typecheck_reports_type_mismatch():
    read = _make_read({("myapp", "prod"): {"PORT": "not-a-number"}})
    result = typecheck_env("myapp", "prod", {"PORT": "int"}, read)
    assert not result.passed
    assert len(result.issues) == 1
    assert result.issues[0].key == "PORT"
    assert result.issues[0].expected_type == "int"


def test_typecheck_skips_missing_keys():
    read = _make_read({("myapp", "prod"): {"HOST": "localhost"}})
    result = typecheck_env("myapp", "prod", {"PORT": "int"}, read)
    assert result.passed
    assert result.checked == 0


def test_typecheck_raises_on_missing_environment():
    read = _make_read({})
    with pytest.raises(TypeCheckError):
        typecheck_env("myapp", "missing", {"PORT": "int"}, read)


def test_typecheck_raises_on_unknown_type():
    read = _make_read({("myapp", "prod"): {"PORT": "8080"}})
    with pytest.raises(TypeCheckError, match="Unknown type"):
        typecheck_env("myapp", "prod", {"PORT": "uuid"}, read)


def test_typecheck_to_dict():
    read = _make_read({("myapp", "prod"): {"PORT": "abc"}})
    result = typecheck_env("myapp", "prod", {"PORT": "int"}, read)
    d = result.to_dict()
    assert d["project"] == "myapp"
    assert d["environment"] == "prod"
    assert d["passed"] is False
    assert len(d["issues"]) == 1
    assert d["issues"][0]["key"] == "PORT"


def test_typecheck_multiple_issues():
    read = _make_read({("app", "dev"): {"PORT": "abc", "ACTIVE": "maybe", "HOST": "localhost"}})
    schema = {"PORT": "int", "ACTIVE": "bool", "HOST": "url"}
    result = typecheck_env("app", "dev", schema, read)
    assert not result.passed
    assert result.checked == 3
    assert len(result.issues) == 3
