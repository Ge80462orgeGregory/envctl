"""CLI command: envctl grep"""

from __future__ import annotations

import json
import sys

import click

from envctl.config import load_config, get_envs_dir
from envctl.env_store import read_env
from envctl.grep import grep_env, GrepError


@click.command("grep")
@click.argument("project")
@click.argument("environment")
@click.argument("pattern")
@click.option("--keys-only", is_flag=True, default=False, help="Search only in keys.")
@click.option("--values-only", is_flag=True, default=False, help="Search only in values.")
@click.option("-i", "--ignore-case", is_flag=True, default=False, help="Case-insensitive matching.")
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
def grep_cmd(
    project: str,
    environment: str,
    pattern: str,
    keys_only: bool,
    values_only: bool,
    ignore_case: bool,
    fmt: str,
) -> None:
    """Search for PATTERN in PROJECT/ENVIRONMENT variables."""
    cfg = load_config()
    envs_dir = get_envs_dir(cfg)

    def _read(p: str, e: str) -> dict:
        return read_env(p, e, envs_dir=envs_dir)

    search_keys = not values_only
    search_values = not keys_only

    try:
        result = grep_env(
            project,
            environment,
            pattern,
            read=_read,
            search_keys=search_keys,
            search_values=search_values,
            ignore_case=ignore_case,
        )
    except GrepError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    if fmt == "json":
        click.echo(json.dumps(result.to_dict(), indent=2))
        return

    if not result.matches:
        click.echo("No matches found.")
        return

    click.echo(f"Found {result.total} match(es) in {project}/{environment}:")
    for m in result.matches:
        click.echo(f"  [{m.matched_on}]  {m.key}={m.value}")
