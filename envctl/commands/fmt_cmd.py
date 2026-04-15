"""CLI command: envctl fmt — pretty-print an environment."""

from __future__ import annotations

import sys
import click

from envctl.config import load_config, get_envs_dir
from envctl.env_store import read_env
from envctl.fmt import format_env, FmtError


@click.command("fmt")
@click.argument("project")
@click.argument("environment")
@click.option(
    "--style",
    "-s",
    default="dotenv",
    show_default=True,
    type=click.Choice(["dotenv", "shell", "json", "table"], case_sensitive=False),
    help="Output format style.",
)
@click.option(
    "--output",
    "-o",
    default=None,
    type=click.Path(writable=True),
    help="Write output to a file instead of stdout.",
)
def fmt_cmd(project: str, environment: str, style: str, output: str | None) -> None:
    """Pretty-print the variables of PROJECT / ENVIRONMENT."""
    cfg = load_config()
    envs_dir = get_envs_dir(cfg)

    variables = read_env(envs_dir, project, environment)

    try:
        result = format_env(project, environment, variables, style=style)  # type: ignore[arg-type]
    except FmtError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    rendered = result.rendered

    if output:
        try:
            with open(output, "w", encoding="utf-8") as fh:
                fh.write(rendered + "\n")
            click.echo(f"Written to {output}")
        except OSError as exc:
            click.echo(f"Error writing file: {exc}", err=True)
            sys.exit(1)
    else:
        click.echo(rendered)
