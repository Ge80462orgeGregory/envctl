"""CLI command: envctl summarize <project> <environment>"""

from __future__ import annotations

import json

import click

from envctl.config import load_config, get_envs_dir
from envctl.env_store import read_env
from envctl.summarize import summarize_env, SummarizeError


@click.command("summarize")
@click.argument("project")
@click.argument("environment")
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["text", "json"]),
    default="text",
    show_default=True,
    help="Output format.",
)
def summarize_cmd(project: str, environment: str, fmt: str) -> None:
    """Display a statistical summary of a project environment."""
    config = load_config()
    envs_dir = get_envs_dir(config)

    def _read(proj: str, env: str):
        return read_env(proj, env, envs_dir=envs_dir)

    try:
        result = summarize_env(project, environment, _read)
    except SummarizeError as exc:
        raise click.ClickException(str(exc))

    if fmt == "json":
        click.echo(json.dumps(result.to_dict(), indent=2))
        return

    click.echo(f"Project     : {result.project}")
    click.echo(f"Environment : {result.environment}")
    click.echo(f"Total keys  : {result.total_keys}")
    click.echo(f"Non-empty   : {result.non_empty_values}")
    click.echo(f"Empty       : {result.empty_values}")
    click.echo(f"Avg val len : {result.avg_value_length:.2f}")
    click.echo(f"Longest key : {result.longest_key}")
    click.echo(f"Shortest key: {result.shortest_key}")
