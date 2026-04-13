"""CLI commands for encrypting and decrypting environment variable values."""

from __future__ import annotations

import click

from envctl.encrypt import EncryptError, decrypt_env, encrypt_env
from envctl.env_store import read_env, write_env


@click.group("encrypt")
def encrypt_cmd() -> None:
    """Encrypt or decrypt values in an environment."""


@encrypt_cmd.command("lock")
@click.argument("project")
@click.argument("environment")
@click.option("--passphrase", "-p", required=True, help="Encryption passphrase.")
@click.option(
    "--key",
    "keys",
    multiple=True,
    help="Specific key(s) to encrypt. Defaults to all keys.",
)
def encrypt_lock(project: str, environment: str, passphrase: str, keys: tuple[str, ...]) -> None:
    """Encrypt variable values in an environment."""
    try:
        result = encrypt_env(
            project=project,
            environment=environment,
            passphrase=passphrase,
            keys=list(keys) if keys else None,
            read=read_env,
            write=write_env,
        )
    except EncryptError as exc:
        raise click.ClickException(str(exc)) from exc

    if result.total_encrypted == 0:
        click.echo("Nothing to encrypt.")
    else:
        click.echo(f"Encrypted {result.total_encrypted} key(s) in '{project}/{environment}'.")
        for k in result.encrypted:
            click.echo(f"  + {k}")
    if result.skipped:
        click.echo(f"Skipped {len(result.skipped)} key(s) (already encrypted or not found).")


@encrypt_cmd.command("unlock")
@click.argument("project")
@click.argument("environment")
@click.option("--passphrase", "-p", required=True, help="Decryption passphrase.")
@click.option(
    "--key",
    "keys",
    multiple=True,
    help="Specific key(s) to decrypt. Defaults to all keys.",
)
def encrypt_unlock(
    project: str, environment: str, passphrase: str, keys: tuple[str, ...]
) -> None:
    """Decrypt variable values in an environment."""
    try:
        result = decrypt_env(
            project=project,
            environment=environment,
            passphrase=passphrase,
            keys=list(keys) if keys else None,
            read=read_env,
            write=write_env,
        )
    except EncryptError as exc:
        raise click.ClickException(str(exc)) from exc

    if result.total_encrypted == 0:
        click.echo("Nothing to decrypt.")
    else:
        click.echo(f"Decrypted {result.total_encrypted} key(s) in '{project}/{environment}'.")
        for k in result.encrypted:
            click.echo(f"  - {k}")
    if result.skipped:
        click.echo(f"Skipped {len(result.skipped)} key(s) (not encrypted or not found).")
