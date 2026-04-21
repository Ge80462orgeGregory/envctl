"""CLI commands for adding or stripping key suffixes."""

import json
import click

from envctl.suffix import add_suffix, strip_suffix, SuffixError
from envctl.env_store import read_env, write_env


def _read(project, environment):
    return read_env(project, environment)


def _write(project, environment, data):
    return write_env(project, environment, data)


@click.group("suffix")
def suffix_cmd():
    """Add or strip a suffix from environment variable keys."""


@suffix_cmd.command("add")
@click.argument("project")
@click.argument("environment")
@click.argument("suffix")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
def suffix_add(project, environment, suffix, as_json):
    """Add SUFFIX to all keys in PROJECT/ENVIRONMENT."""
    try:
        result = add_suffix(project, environment, suffix, read_fn=_read, write_fn=_write)
    except SuffixError as exc:
        raise click.ClickException(str(exc))

    if as_json:
        click.echo(json.dumps(result.to_dict(), indent=2))
        return

    if result.total_changed == 0:
        click.echo("No keys were changed.")
    else:
        click.echo(f"Added suffix '{suffix}' to {result.total_changed} key(s).")
        for key in result.changed:
            click.echo(f"  {key}  ->  {key}{suffix}")
    if result.skipped:
        click.echo(f"Skipped {len(result.skipped)} key(s) to avoid collision.")


@suffix_cmd.command("strip")
@click.argument("project")
@click.argument("environment")
@click.argument("suffix")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
def suffix_strip(project, environment, suffix, as_json):
    """Strip SUFFIX from all matching keys in PROJECT/ENVIRONMENT."""
    try:
        result = strip_suffix(project, environment, suffix, read_fn=_read, write_fn=_write)
    except SuffixError as exc:
        raise click.ClickException(str(exc))

    if as_json:
        click.echo(json.dumps(result.to_dict(), indent=2))
        return

    if result.total_changed == 0:
        click.echo(f"No keys ended with '{suffix}'.")
    else:
        click.echo(f"Stripped suffix '{suffix}' from {result.total_changed} key(s).")
        for key in result.changed:
            click.echo(f"  {key}  ->  {key[:-len(suffix)]}")
    if result.skipped:
        click.echo(f"Left {len(result.skipped)} key(s) unchanged (no matching suffix).")
