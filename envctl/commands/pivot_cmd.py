"""CLI command: envctl pivot."""

from __future__ import annotations

import json

import click

from envctl.config import get_envs_dir, load_config
from envctl.env_store import list_environments, read_env
from envctl.pivot import PivotError, pivot_env


def _read(project: str, env: str) -> dict:
    cfg = load_config()
    envs_dir = get_envs_dir(cfg)
    return read_env(envs_dir, project, env)


def _list_envs(project: str) -> list:
    cfg = load_config()
    envs_dir = get_envs_dir(cfg)
    return list_environments(envs_dir, project)


@click.command("pivot")
@click.argument("project")
@click.option(
    "--env",
    "environments",
    multiple=True,
    help="Environments to include (repeatable). Defaults to all.",
)
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["text", "json"]),
    default="text",
    show_default=True,
    help="Output format.",
)
def pivot_cmd(project: str, environments: tuple, fmt: str) -> None:
    """Show a pivot table of keys across environments for PROJECT."""
    try:
        result = pivot_env(
            project=project,
            environments=list(environments),
            read_env=_read,
            list_environments=_list_envs,
        )
    except PivotError as exc:
        raise click.ClickException(str(exc)) from exc

    if fmt == "json":
        click.echo(json.dumps(result.to_dict(), indent=2))
        return

    if not result.rows:
        click.echo(f"No keys found for project '{project}'.")
        return

    col_width = max(len(e) for e in result.environments) + 2
    key_width = max(len(r.key) for r in result.rows) + 2

    header = f"{'KEY':<{key_width}}" + "".join(
        f"{e:<{col_width}}" for e in result.environments
    )
    click.echo(header)
    click.echo("-" * len(header))

    for row in result.rows:
        line = f"{row.key:<{key_width}}"
        for env in result.environments:
            val = row.values.get(env)
            cell = "(missing)" if val is None else val
            line += f"{cell:<{col_width}}"
        click.echo(line)

    click.echo(f"\n{result.total_keys} keys, {result.total_missing} missing cell(s).")
