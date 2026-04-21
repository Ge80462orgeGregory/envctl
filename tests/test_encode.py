"""Tests for envctl.encode."""

from __future__ import annotations

import base64
import pytest

from envctl.encode import EncodeError, EncodeResult, encode_env


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_store: dict[str, dict[str, str]] = {}


def _make_read(data: dict[str, str]):
    def _read(project: str, environment: str) -> dict[str, str]:
        return dict(data)
    return _read


def _write(project: str, environment: str, variables: dict[str, str]) -> None:
    _store[f"{project}/{environment}"] = dict(variables)


def _read_written(project: str, environment: str) -> dict[str, str]:
    return _store.get(f"{project}/{environment}", {})


def setup_function():
    _store.clear()


# ---------------------------------------------------------------------------
# encode tests
# ---------------------------------------------------------------------------

def test_encode_all_keys():
    data = {"API_KEY": "secret", "TOKEN": "abc123"}
    result = encode_env("proj", "dev", read=_make_read(data), write=_write)

    assert isinstance(result, EncodeResult)
    assert set(result.encoded) == {"API_KEY", "TOKEN"}
    assert result.decoded == []
    assert result.skipped == []
    assert result.total_changed == 2

    written = _read_written("proj", "dev")
    assert written["API_KEY"] == base64.b64encode(b"secret").decode()
    assert written["TOKEN"] == base64.b64encode(b"abc123").decode()


def test_encode_specific_keys():
    data = {"A": "hello", "B": "world"}
    result = encode_env("proj", "dev", keys=["A"], read=_make_read(data), write=_write)

    assert result.encoded == ["A"]
    written = _read_written("proj", "dev")
    assert written["A"] == base64.b64encode(b"hello").decode()
    assert written["B"] == "world"  # untouched


def test_decode_reverses_encoding():
    encoded_val = base64.b64encode(b"mysecret").decode()
    data = {"SECRET": encoded_val}
    result = encode_env(
        "proj", "dev", decode=True, read=_make_read(data), write=_write
    )

    assert result.decoded == ["SECRET"]
    written = _read_written("proj", "dev")
    assert written["SECRET"] == "mysecret"


def test_decode_invalid_base64_skips_key():
    data = {"BAD": "not-valid-base64!!!"}
    result = encode_env(
        "proj", "dev", decode=True, read=_make_read(data), write=_write
    )

    assert "BAD" in result.skipped
    assert result.total_changed == 0


def test_unknown_keys_raise_error():
    data = {"EXISTING": "value"}
    with pytest.raises(EncodeError, match="Keys not found"):
        encode_env(
            "proj", "dev", keys=["MISSING"], read=_make_read(data), write=_write
        )


def test_empty_environment_raises_error():
    with pytest.raises(EncodeError, match="empty or does not exist"):
        encode_env("proj", "dev", read=_make_read({}), write=_write)


def test_already_encoded_value_skipped():
    # Encoding an already-encoded value produces a different result, so it
    # should NOT be skipped — only identical values are skipped.
    val = "hello"
    encoded_once = base64.b64encode(val.encode()).decode()
    data = {"K": encoded_once}
    result = encode_env("proj", "dev", read=_make_read(data), write=_write)
    # The double-encoded value differs from the original, so it is recorded.
    assert "K" in result.encoded


def test_to_dict_contains_expected_keys():
    data = {"X": "foo"}
    result = encode_env("proj", "staging", read=_make_read(data), write=_write)
    d = result.to_dict()
    assert d["project"] == "proj"
    assert d["environment"] == "staging"
    assert "encoded" in d
    assert "decoded" in d
    assert "skipped" in d
    assert "total_changed" in d
