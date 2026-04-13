"""Tests for envctl.encrypt module."""

from __future__ import annotations

import pytest

from envctl.encrypt import (
    ENCRYPTED_PREFIX,
    EncryptError,
    EncryptResult,
    _derive_key,
    _xor_decrypt,
    _xor_encrypt,
    decrypt_env,
    encrypt_env,
)

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
# Low-level crypto helpers
# ---------------------------------------------------------------------------

def test_xor_roundtrip():
    key = _derive_key("secret")
    original = "hello_world"
    assert _xor_decrypt(_xor_encrypt(original, key), key) == original


def test_derive_key_is_32_bytes():
    assert len(_derive_key("any-passphrase")) == 32


# ---------------------------------------------------------------------------
# encrypt_env
# ---------------------------------------------------------------------------

def test_encrypt_all_keys():
    data = {"DB_URL": "postgres://localhost", "SECRET": "abc123"}
    result = encrypt_env("myapp", "prod", "pass", None, _make_read(data), _write)
    written = _read_written("myapp", "prod")
    assert result.total_encrypted == 2
    assert all(v.startswith(ENCRYPTED_PREFIX) for v in written.values())


def test_encrypt_specific_keys():
    data = {"DB_URL": "postgres://localhost", "SECRET": "abc123"}
    result = encrypt_env("myapp", "prod", "pass", ["SECRET"], _make_read(data), _write)
    written = _read_written("myapp", "prod")
    assert result.total_encrypted == 1
    assert written["SECRET"].startswith(ENCRYPTED_PREFIX)
    assert not written["DB_URL"].startswith(ENCRYPTED_PREFIX)


def test_encrypt_skips_already_encrypted():
    data = {"KEY": ENCRYPTED_PREFIX + "somehash"}
    result = encrypt_env("p", "e", "pass", None, _make_read(data), _write)
    assert result.total_encrypted == 0
    assert "KEY" in result.skipped


def test_encrypt_skips_missing_keys():
    data = {"A": "1"}
    result = encrypt_env("p", "e", "pass", ["MISSING"], _make_read(data), _write)
    assert result.total_encrypted == 0
    assert "MISSING" in result.skipped


def test_encrypt_empty_passphrase_raises():
    with pytest.raises(EncryptError, match="Passphrase"):
        encrypt_env("p", "e", "", None, _make_read({"K": "v"}), _write)


def test_encrypt_empty_env_raises():
    with pytest.raises(EncryptError):
        encrypt_env("p", "e", "pass", None, _make_read({}), _write)


# ---------------------------------------------------------------------------
# decrypt_env
# ---------------------------------------------------------------------------

def test_decrypt_roundtrip():
    data = {"SECRET": "my-secret-value"}
    encrypt_env("p", "e", "pass", None, _make_read(data), _write)
    encrypted_data = _read_written("p", "e")
    result = decrypt_env("p", "e", "pass", None, _make_read(encrypted_data), _write)
    final = _read_written("p", "e")
    assert result.total_encrypted == 1
    assert final["SECRET"] == "my-secret-value"


def test_decrypt_skips_plain_values():
    data = {"KEY": "plain"}
    result = decrypt_env("p", "e", "pass", None, _make_read(data), _write)
    assert result.total_encrypted == 0
    assert "KEY" in result.skipped


def test_decrypt_empty_passphrase_raises():
    with pytest.raises(EncryptError, match="Passphrase"):
        decrypt_env("p", "e", "", None, _make_read({"K": "v"}), _write)
