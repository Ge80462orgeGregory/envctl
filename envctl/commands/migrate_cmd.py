"""CLI command for migrating environment variables between projects/environments."""

import json
import click
from envctl.migrate import migrate_env, MigrateError
from envctl.env_store import read_env, write_env
from envctl.config import load_config, get_envs_dir


@click.command("migrate")
@click.argument("source_project")
@click.argument("source_env")
@click.argument("target_project")
@click.argument("target_env")
@click.option("--key", "keys", multiple=True, help="Specific keys to migrate (default: all).")
@click.option(
    "--remap",
    "remaps",
    multiple=True,
    metavar="OLD:NEW",
    help="Remap a key name during migration, e.g. DB_HOST:DATABASE_HOST.",
)
@click.option("--overwrite", is_flag=True, default=False, help="Overwrite existing keys in target.")
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
def migrate_cmd(source_project, source_env, target_project, target_env, keys, remaps, overwrite, fmt):
    """Migrate env vars from SOURCE_PROJECT/SOURCE_ENV to TARGET_PROJECT/TARGET_ENV."""
    config = load_config()
    envs_dir = get_envs_dir(config)

    key_map = {}
    for remap in remaps:
        if ":" not in remap:
            raise click.BadParameter(f"Remap '{remap}' must be in OLD:NEW format.")
        old, new = remap.split(":", 1)
        key_map[old] = new

    def _read(project, env):
        return read_env(envs_dir, project, env)

    def _write(project, env, data):
        write_env(envs_dir, project, env, data)

    try:
        result = migrate_env(
            source_project=source_project,
            source_env=source_env,
            target_project=target_project,
            target_env=target_env,
            read_env=_read,
            write_env=_write,
            key_map=key_map or None,
            keys=list(keys) if keys else None,
            overwrite=overwrite,
        )
    except MigrateError as exc:
        raise click.ClickException(str(exc))

    if fmt == "json":
        click.echo(json.dumps(result.to_dict(), indent=2))
        return

    if result.total_migrated == 0:
        click.echo("Nothing to migrate.")
        return

    click.echo(f"Migrated {result.total_migrated} key(s) to '{target_project}/{target_env}'.")
    for dest_key, value in result.migrated.items():
        src_key = {v: k for k, v in result.remapped.items()}.get(dest_key, dest_key)
        remap_note = f" (remapped from '{src_key}')" if dest_key in result.remapped.values() else ""
        click.echo(f"  {dest_key}={value}{remap_note}")
    if result.total_skipped:
        click.echo(f"Skipped {result.total_skipped} existing key(s) (use --overwrite to replace).")
