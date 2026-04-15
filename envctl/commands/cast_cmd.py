"""CLI command: envctl cast — type-cast env var values."""
from __future__ import annotations

import json
import sys

import click

from envctl.cast import CastError, cast_env
from envctl.config import get_envs_dir, load_config
from envctl.env_store import read_env, write_env


@click.command("cast")
@click.argument("project")
@click.argument("environment")
@click.option(
    "-c", "--cast",
    "casts",
    metavar="KEY:TYPE",
    multiple=True,
    required=True,
    help="Key and target type, e.g. PORT:int.  Repeatable.",
)
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
def cast_cmd(project: str, environment: str, casts: tuple, fmt: str) -> None:
    """Type-cast values of specific keys in PROJECT/ENVIRONMENT.

    Supported types: int, float, bool, str, upper, lower, strip.
    """
    config = load_config()
    envs_dir = get_envs_dir(config)

    def _read(p, e):
        return read_env(p, e, envs_dir)

    def _write(p, e, d):
        write_env(p, e, d, envs_dir)

    cast_map: dict[str, str] = {}
    for item in casts:
        if ":" not in item:
            raise click.UsageError(f"Invalid cast spec '{item}'. Use KEY:TYPE.")
        key, _, type_name = item.partition(":")
        cast_map[key.strip()] = type_name.strip()

    try:
        result = cast_env(project, environment, cast_map, _read, _write)
    except CastError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    if fmt == "json":
        click.echo(json.dumps(result.to_dict(), indent=2))
        return

    if result.cast:
        for key, val in result.cast.items():
            click.echo(f"  cast  {key} -> {val}")
    if result.skipped:
        for key in result.skipped:
            click.echo(f"  skip  {key} (not found)")
    if result.errors:
        for msg in result.errors:
            click.echo(f"  error {msg}", err=True)

    click.echo(
        f"\nCast {result.total_cast} key(s) in "
        f"{project}/{environment}."
    )
    if result.errors:
        sys.exit(1)
