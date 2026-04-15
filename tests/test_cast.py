"""Unit tests for envctl/cast.py."""
from __future__ import annotations

import pytest

from envctl.cast import CastError, CastResult, cast_env


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_read(store: dict):
    def _read(project, environment):
        return dict(store.get((project, environment), {}))
    return _read


_written: dict = {}


def _write(project, environment, data):
    _written[(project, environment)] = dict(data)


def setup_function():
    _written.clear()


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------

def test_cast_int_converts_string():
    store = {("app", "dev"): {"PORT": "8080", "NAME": "app"}}
    result = cast_env("app", "dev", {"PORT": "int"}, _make_read(store), _write)
    assert result.cast == {"PORT": "8080"}
    assert _written[("app", "dev")]["PORT"] == "8080"


def test_cast_upper_transforms_value():
    store = {("app", "dev"): {"ENV": "production"}}
    result = cast_env("app", "dev", {"ENV": "upper"}, _make_read(store), _write)
    assert result.cast["ENV"] == "PRODUCTION"


def test_cast_lower_transforms_value():
    store = {("app", "dev"): {"ENV": "STAGING"}}
    result = cast_env("app", "dev", {"ENV": "lower"}, _make_read(store), _write)
    assert result.cast["ENV"] == "staging"


def test_cast_strip_removes_whitespace():
    store = {("app", "dev"): {"KEY": "  hello  "}}
    result = cast_env("app", "dev", {"KEY": "strip"}, _make_read(store), _write)
    assert result.cast["KEY"] == "hello"


def test_cast_bool_truthy_value():
    store = {("app", "dev"): {"DEBUG": "true"}}
    result = cast_env("app", "dev", {"DEBUG": "bool"}, _make_read(store), _write)
    assert result.cast["DEBUG"] == "True"


def test_cast_bool_falsy_value():
    store = {("app", "dev"): {"DEBUG": "false"}}
    result = cast_env("app", "dev", {"DEBUG": "bool"}, _make_read(store), _write)
    assert result.cast["DEBUG"] == "False"


def test_missing_key_goes_to_skipped():
    store = {("app", "dev"): {"A": "1"}}
    result = cast_env("app", "dev", {"MISSING": "int"}, _make_read(store), _write)
    assert "MISSING" in result.skipped
    assert result.total_cast == 0
    assert ("app", "dev") not in _written


def test_invalid_int_goes_to_errors():
    store = {("app", "dev"): {"PORT": "not-a-number"}}
    result = cast_env("app", "dev", {"PORT": "int"}, _make_read(store), _write)
    assert len(result.errors) == 1
    assert "PORT" in result.errors[0]


def test_unknown_type_raises_cast_error():
    store = {("app", "dev"): {"KEY": "value"}}
    with pytest.raises(CastError, match="Unknown cast type"):
        cast_env("app", "dev", {"KEY": "uuid"}, _make_read(store), _write)


def test_to_dict_structure():
    store = {("p", "e"): {"X": "1"}}
    result = cast_env("p", "e", {"X": "float"}, _make_read(store), _write)
    d = result.to_dict()
    assert d["project"] == "p"
    assert d["environment"] == "e"
    assert "cast" in d
    assert "skipped" in d
    assert "errors" in d
    assert "total_cast" in d
