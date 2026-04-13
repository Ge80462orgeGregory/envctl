"""CLI command for reordering environment variable keys."""

from __future__ import annotations

import json
import sys

import click

from envctl.config import load_config, get_envs_dir
from envctl.env_store import read_env, write_env
from envctl.reorder import ReorderError, reorder_env


@click.command("reorder")
@click.argument("project")
@click.argument("environment")
@click.option(
    "--keys",
    "key_order",
    default=None,
    help="Comma-separated list of keys to place first, in order.",
)
@click.option(
    "--reverse",
    is_flag=True,
    default=False,
    help="Sort keys in reverse alphabetical order.",
)
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    default=False,
    help="Output result as JSON.",
)
def reorder_cmd(
    project: str,
    environment: str,
    key_order: str | None,
    reverse: bool,
    as_json: bool,
) -> None:
    """Reorder keys in PROJECT/ENVIRONMENT alphabetically or by a custom order."""
    cfg = load_config()
    envs_dir = get_envs_dir(cfg)

    parsed_order = (
        [k.strip() for k in key_order.split(",") if k.strip()]
        if key_order
        else None
    )

    try:
        result = reorder_env(
            project,
            environment,
            read_env=lambda p, e: read_env(p, e, envs_dir=envs_dir),
            write_env=lambda p, e, v: write_env(p, e, v, envs_dir=envs_dir),
            key_order=parsed_order,
            reverse=reverse,
        )
    except ReorderError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    if as_json:
        click.echo(json.dumps(result.to_dict(), indent=2))
        return

    if not result.changed:
        click.echo("No changes — keys are already in the desired order.")
    else:
        click.echo(
            f"Reordered {len(result.new_order)} keys in "
            f"'{project}/{environment}'."
        )
        for key in result.new_order:
            click.echo(f"  {key}")
