"""CLI command for detecting unresolved placeholders in an environment."""

from __future__ import annotations

import json
import sys

import click

from envctl.commands import cli
from envctl.config import load_config, get_envs_dir
from envctl.env_store import read_env
from envctl.placeholder import find_placeholders, PlaceholderError


@cli.command("placeholder")
@click.argument("project")
@click.argument("environment")
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text", show_default=True)
def placeholder_cmd(project: str, environment: str, fmt: str) -> None:
    """Find unresolved placeholder variables (e.g. ${VAR}) in an environment."""
    config = load_config()
    envs_dir = get_envs_dir(config)

    def _read(proj: str, env: str) -> dict[str, str]:
        return read_env(envs_dir, proj, env)

    try:
        result = find_placeholders(project, environment, _read)
    except PlaceholderError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    if fmt == "json":
        click.echo(json.dumps(result.to_dict(), indent=2))
        return

    if not result.has_unresolved:
        click.echo(f"No unresolved placeholders found in {project}/{environment}.")
        return

    click.echo(f"Unresolved placeholders in {project}/{environment} ({result.total} key(s)):")
    for match in result.matches:
        refs = ", ".join(match.placeholders)
        click.echo(f"  {match.key} = {match.value!r}  ->  [{refs}]")
