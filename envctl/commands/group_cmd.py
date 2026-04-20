"""CLI command for grouping environment variables by prefix."""

from __future__ import annotations

import json

import click

from envctl.group import GroupError, group_env
from envctl.env_store import read_env
from envctl.config import load_config, get_envs_dir


def _read(project: str, environment: str):
    config = load_config()
    envs_dir = get_envs_dir(config)
    return read_env(envs_dir, project, environment)


@click.command("group")
@click.argument("project")
@click.argument("environment")
@click.option(
    "--prefix",
    "prefixes",
    multiple=True,
    help="Prefix(es) to group by. Repeatable. Auto-detected if omitted.",
)
@click.option("--separator", default="_", show_default=True, help="Key segment separator.")
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text", show_default=True)
def group_cmd(project: str, environment: str, prefixes, separator: str, fmt: str):
    """Group environment variables by shared key prefix."""
    try:
        result = group_env(
            project,
            environment,
            _read,
            prefixes=list(prefixes) if prefixes else None,
            separator=separator,
        )
    except GroupError as exc:
        raise click.ClickException(str(exc))

    if fmt == "json":
        click.echo(json.dumps(result.to_dict(), indent=2))
        return

    if not result.groups and not result.ungrouped:
        click.echo("No variables found.")
        return

    for group_name, keys in sorted(result.groups.items()):
        click.echo(f"[{group_name}]")
        for k, v in sorted(keys.items()):
            click.echo(f"  {k}={v}")

    if result.ungrouped:
        click.echo("[ungrouped]")
        for k, v in sorted(result.ungrouped.items()):
            click.echo(f"  {k}={v}")

    click.echo(
        f"\n{result.total_groups()} group(s), {result.total_keys()} total key(s)."
    )
