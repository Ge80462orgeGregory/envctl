"""CLI command: substitute values in an environment from a source environment."""
from __future__ import annotations

import json
import sys

import click

from envctl.substitute import SubstituteError, substitute_env
from envctl.env_store import read_env, write_env


@click.command("substitute")
@click.argument("project")
@click.argument("target_env")
@click.option("--from-project", "src_project", default=None, help="Source project (defaults to same project).")
@click.option("--from-env", "src_env", required=True, help="Source environment to pull values from.")
@click.option("--keys", "-k", multiple=True, default=None, help="Specific keys to substitute (repeatable).")
@click.option("--no-overwrite", is_flag=True, default=False, help="Skip keys that already have a non-empty value.")
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
def substitute_cmd(ctx, project, target_env, src_project, src_env, keys, no_overwrite, fmt):
    """Substitute values in TARGET_ENV with values from a source environment."""
    src_project = src_project or project
    try:
        source_values = read_env(src_project, src_env)
        if not source_values:
            click.echo(f"Source environment '{src_project}/{src_env}' is empty.", err=True)
            sys.exit(1)

        result = substitute_env(
            project=project,
            environment=target_env,
            source_values=source_values,
            read_env=read_env,
            write_env=write_env,
            keys=list(keys) if keys else None,
            overwrite=not no_overwrite,
        )
    except SubstituteError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    if fmt == "json":
        click.echo(json.dumps(result.to_dict(), indent=2))
        return

    if result.total_substituted == 0:
        click.echo("Nothing substituted.")
    else:
        click.echo(f"Substituted {result.total_substituted} key(s) in '{project}/{target_env}':")
        for key, val in result.substituted.items():
            click.echo(f"  {key} = {val}")

    if result.skipped:
        click.echo(f"Skipped {len(result.skipped)} key(s):")
        for key, reason in result.skipped.items():
            click.echo(f"  {key}: {reason}")
