"""CLI commands for protecting and unprotecting environment variable keys."""

from __future__ import annotations

import click

from envctl.config import load_config, get_envs_dir
from envctl.env_store import read_env, write_env
from envctl.protect import ProtectError, protect_keys, unprotect_keys, _load_protected


@click.group("protect")
def protect_cmd():
    """Protect or unprotect environment variable keys from being overwritten."""


@protect_cmd.command("add")
@click.argument("project")
@click.argument("environment")
@click.argument("keys", nargs=-1, required=True)
def protect_add(project: str, environment: str, keys: tuple):
    """Mark KEY(s) as protected in PROJECT/ENVIRONMENT."""
    config = load_config()
    envs_dir = get_envs_dir(config)

    def _read(p, e):
        return read_env(p, e, envs_dir)

    def _write(p, e, data):
        write_env(p, e, data, envs_dir)

    try:
        result = protect_keys(project, environment, list(keys), _read, _write)
    except ProtectError as exc:
        raise click.ClickException(str(exc))

    if result.newly_protected:
        click.echo(f"Protected: {', '.join(result.newly_protected)}")
    if result.already_protected:
        click.echo(f"Already protected: {', '.join(result.already_protected)}")
    if result.not_found:
        click.echo(f"Not found (skipped): {', '.join(result.not_found)}")
    if not result.newly_protected:
        click.echo("No new keys were protected.")


@protect_cmd.command("remove")
@click.argument("project")
@click.argument("environment")
@click.argument("keys", nargs=-1, required=True)
def protect_remove(project: str, environment: str, keys: tuple):
    """Remove protection from KEY(s) in PROJECT/ENVIRONMENT."""
    config = load_config()
    envs_dir = get_envs_dir(config)

    def _read(p, e):
        return read_env(p, e, envs_dir)

    def _write(p, e, data):
        write_env(p, e, data, envs_dir)

    try:
        result = unprotect_keys(project, environment, list(keys), _read, _write)
    except ProtectError as exc:
        raise click.ClickException(str(exc))

    if result.newly_unprotected:
        click.echo(f"Unprotected: {', '.join(result.newly_unprotected)}")
    if result.not_found:
        click.echo(f"Not protected (skipped): {', '.join(result.not_found)}")
    if not result.newly_unprotected:
        click.echo("No keys were unprotected.")


@protect_cmd.command("list")
@click.argument("project")
@click.argument("environment")
def protect_list(project: str, environment: str):
    """List all protected keys in PROJECT/ENVIRONMENT."""
    config = load_config()
    envs_dir = get_envs_dir(config)
    env = read_env(project, environment, envs_dir)
    protected = _load_protected(env)
    if protected:
        for key in sorted(protected):
            click.echo(key)
    else:
        click.echo("No protected keys.")
