"""Tests for the encrypt CLI commands."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from click.testing import CliRunner

from envctl.commands.encrypt_cmd import encrypt_cmd
from envctl.encrypt import EncryptError, EncryptResult


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def _patch(func_name: str, result):
    return patch(f"envctl.commands.encrypt_cmd.{func_name}", return_value=result)


# ---------------------------------------------------------------------------
# encrypt lock
# ---------------------------------------------------------------------------

def test_encrypt_lock_success(runner):
    result = EncryptResult(project="app", environment="prod", encrypted=["SECRET", "TOKEN"])
    with _patch("encrypt_env", result):
        out = runner.invoke(encrypt_cmd, ["lock", "app", "prod", "--passphrase", "s3cr3t"])
    assert out.exit_code == 0
    assert "Encrypted 2 key(s)" in out.output
    assert "+ SECRET" in out.output


def test_encrypt_lock_nothing_to_encrypt(runner):
    result = EncryptResult(project="app", environment="prod", skipped=["KEY"])
    with _patch("encrypt_env", result):
        out = runner.invoke(encrypt_cmd, ["lock", "app", "prod", "--passphrase", "s3cr3t"])
    assert out.exit_code == 0
    assert "Nothing to encrypt" in out.output


def test_encrypt_lock_error(runner):
    with patch(
        "envctl.commands.encrypt_cmd.encrypt_env",
        side_effect=EncryptError("No variables found"),
    ):
        out = runner.invoke(encrypt_cmd, ["lock", "app", "prod", "--passphrase", "s3cr3t"])
    assert out.exit_code != 0
    assert "No variables found" in out.output


def test_encrypt_lock_specific_keys(runner):
    result = EncryptResult(project="app", environment="prod", encrypted=["SECRET"])
    with patch("envctl.commands.encrypt_cmd.encrypt_env", return_value=result) as mock:
        out = runner.invoke(
            encrypt_cmd,
            ["lock", "app", "prod", "--passphrase", "s3cr3t", "--key", "SECRET"],
        )
    assert out.exit_code == 0
    _, kwargs = mock.call_args
    assert kwargs.get("keys") == ["SECRET"] or mock.call_args[0][3] == ["SECRET"]


# ---------------------------------------------------------------------------
# encrypt unlock
# ---------------------------------------------------------------------------

def test_encrypt_unlock_success(runner):
    result = EncryptResult(project="app", environment="prod", encrypted=["SECRET"])
    with _patch("decrypt_env", result):
        out = runner.invoke(encrypt_cmd, ["unlock", "app", "prod", "--passphrase", "s3cr3t"])
    assert out.exit_code == 0
    assert "Decrypted 1 key(s)" in out.output
    assert "- SECRET" in out.output


def test_encrypt_unlock_nothing_to_decrypt(runner):
    result = EncryptResult(project="app", environment="prod", skipped=["PLAIN"])
    with _patch("decrypt_env", result):
        out = runner.invoke(encrypt_cmd, ["unlock", "app", "prod", "--passphrase", "s3cr3t"])
    assert out.exit_code == 0
    assert "Nothing to decrypt" in out.output


def test_encrypt_unlock_error(runner):
    with patch(
        "envctl.commands.encrypt_cmd.decrypt_env",
        side_effect=EncryptError("Bad passphrase"),
    ):
        out = runner.invoke(encrypt_cmd, ["unlock", "app", "prod", "--passphrase", "wrong"])
    assert out.exit_code != 0
    assert "Bad passphrase" in out.output
