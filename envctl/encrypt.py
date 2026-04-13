"""Encrypt and decrypt environment variable values using a passphrase."""

from __future__ import annotations

import base64
import hashlib
import os
from dataclasses import dataclass, field
from typing import Callable


class EncryptError(Exception):
    pass


@dataclass
class EncryptResult:
    project: str
    environment: str
    encrypted: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)

    @property
    def total_encrypted(self) -> int:
        return len(self.encrypted)


def _derive_key(passphrase: str) -> bytes:
    """Derive a 32-byte key from a passphrase using SHA-256."""
    return hashlib.sha256(passphrase.encode()).digest()


def _xor_encrypt(value: str, key: bytes) -> str:
    """XOR-based encryption encoded as base64 (lightweight, no external deps)."""
    value_bytes = value.encode()
    key_stream = (key[i % len(key)] for i in range(len(value_bytes)))
    encrypted = bytes(b ^ k for b, k in zip(value_bytes, key_stream))
    return base64.b64encode(encrypted).decode()


def _xor_decrypt(token: str, key: bytes) -> str:
    """Reverse of _xor_encrypt."""
    encrypted = base64.b64decode(token.encode())
    key_stream = (key[i % len(key)] for i in range(len(encrypted)))
    decrypted = bytes(b ^ k for b, k in zip(encrypted, key_stream))
    return decrypted.decode()


ENCRYPTED_PREFIX = "enc:"


def encrypt_env(
    project: str,
    environment: str,
    passphrase: str,
    keys: list[str] | None,
    read: Callable[[str, str], dict[str, str]],
    write: Callable[[str, str, dict[str, str]], None],
) -> EncryptResult:
    if not passphrase:
        raise EncryptError("Passphrase must not be empty.")

    variables = read(project, environment)
    if not variables:
        raise EncryptError(f"No variables found for '{project}/{environment}'.")

    key = _derive_key(passphrase)
    result = EncryptResult(project=project, environment=environment)
    updated = dict(variables)

    target_keys = keys if keys else list(variables.keys())

    for k in target_keys:
        if k not in variables:
            result.skipped.append(k)
            continue
        val = variables[k]
        if val.startswith(ENCRYPTED_PREFIX):
            result.skipped.append(k)
            continue
        updated[k] = ENCRYPTED_PREFIX + _xor_encrypt(val, key)
        result.encrypted.append(k)

    write(project, environment, updated)
    return result


def decrypt_env(
    project: str,
    environment: str,
    passphrase: str,
    keys: list[str] | None,
    read: Callable[[str, str], dict[str, str]],
    write: Callable[[str, str, dict[str, str]], None],
) -> EncryptResult:
    if not passphrase:
        raise EncryptError("Passphrase must not be empty.")

    variables = read(project, environment)
    if not variables:
        raise EncryptError(f"No variables found for '{project}/{environment}'.")

    key = _derive_key(passphrase)
    result = EncryptResult(project=project, environment=environment)
    updated = dict(variables)

    target_keys = keys if keys else list(variables.keys())

    for k in target_keys:
        if k not in variables:
            result.skipped.append(k)
            continue
        val = variables[k]
        if not val.startswith(ENCRYPTED_PREFIX):
            result.skipped.append(k)
            continue
        try:
            updated[k] = _xor_decrypt(val[len(ENCRYPTED_PREFIX):], key)
            result.encrypted.append(k)
        except Exception as exc:
            raise EncryptError(f"Failed to decrypt key '{k}': {exc}") from exc

    write(project, environment, updated)
    return result
