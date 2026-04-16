"""Tests for envctl.swap."""
import pytest
from envctl.swap import swap_keys, SwapError, SwapResult

_store: dict = {}


def _make_read(data: dict):
    def _read(project, environment):
        return dict(data.get((project, environment), {}))
    return _read


def _write(project, environment, env):
    _store[(project, environment)] = dict(env)


def _read_written(project, environment):
    return _store.get((project, environment), {})


def setup_function():
    _store.clear()


def test_swap_exchanges_values():
    data = {("proj", "dev"): {"A": "hello", "B": "world"}}
    result = swap_keys("proj", "dev", "A", "B", _make_read(data), _write)
    written = _read_written("proj", "dev")
    assert written["A"] == "world"
    assert written["B"] == "hello"


def test_swap_result_fields():
    data = {("proj", "dev"): {"X": "foo", "Y": "bar"}}
    result = swap_keys("proj", "dev", "X", "Y", _make_read(data), _write)
    assert isinstance(result,.key_a == "X"
    assert result.key_b == "Y"
    assert result.value_a == "foo"
    assert result.value_b == "bar"


def test_swap_to_dict():
    data = {("p", "e"): {"K1": "v1", "K2": "v2"}}
    result = swap_keys("p", "e", "K1", "K2", _make_read(data), _write)
    d = result.to_dict()
    assert d["project"] == "p"
    assert d["environment"] == "e"
    assert d["key_a"] == "K1"
    assert d["key_b"] == "K2"


def test_swap_same_key_raises():
    data = {("proj", "dev"): {"A": "val"}}
    with pytest.raises(SwapError, match="Cannot swap a key with itself"):
        swap_keys("proj", "dev", "A", "A", _make_read(data), _write)


def test_swap_missing_key_a_raises():
    data = {("proj", "dev"): {"B": "val"}}
    with pytest.raises(SwapError, match="Key 'A' not found"):
        swap_keys("proj", "dev", "A", "B", _make_read(data), _write)


def test_swap_missing_key_b_raises():
    data = {("proj", "dev"): {"A": "val"}}
    with pytest.raises(SwapError, match="Key 'B' not found"):
        swap_keys("proj", "dev", "A", "B", _make_read(data), _write)


def test_swap_preserves_other_keys():
    data = {("proj", "dev"): {"A": "1", "B": "2", "C": "3"}}
    swap_keys("proj", "dev", "A", "B", _make_read(data), _write)
    written = _read_written("proj", "dev")
    assert written["C"] == "3"
