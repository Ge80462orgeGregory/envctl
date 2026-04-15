"""CLI command for annotating environment variable keys."""

from __future__ import annotations

import json

import click

from envctl.annotate import AnnotateError, annotate_env
from envctl.config import get_envs_dir
from envctl.env_store import read_env, write_env


def _read(project: str, environment: str) -> dict[str, str]:
    return read_env(get_envs_dir(), project, environment)


def _write(project: str, environment: str, data: dict[str, str]) -> None:
    write_env(get_envs_dir(), project, environment, data)


@click.command("annotate")
@click.argument("project")
@click.argument("environment")
@click.option("-s", "--set", "sets", multiple=True, metavar="KEY=DESC",
              help="Set annotation: KEY=Description text")
@click.option("-r", "--remove", "removes", multiple=True, metavar="KEY",
              help="Remove annotation for KEY")
@click.option("--json", "as_json", is_flag=True, default=False,
              help="Output result as JSON")
def annotate_cmd(
    project: str,
    environment: str,
    sets: tuple[str, ...],
    removes: tuple[str, ...],
    as_json: bool,
) -> None:
    """Annotate keys in PROJECT/ENVIRONMENT with descriptions."""
    descriptions: dict[str, str] = {}
    for item in sets:
        if "=" not in item:
            raise click.BadParameter(f"Expected KEY=DESC, got: {item}", param_hint="--set")
        key, _, desc = item.partition("=")
        descriptions[key.strip()] = desc.strip()

    if not descriptions and not removes:
        raise click.UsageError("Provide at least one --set or --remove option.")

    try:
        result = annotate_env(
            _read, _write, project, environment,
            descriptions=descriptions,
            remove_keys=list(removes),
        )
    except AnnotateError as exc:
        raise click.ClickException(str(exc)) from exc

    if as_json:
        click.echo(json.dumps(result.to_dict(), indent=2))
        return

    if result.total_changes == 0:
        click.echo("No annotation changes made.")
        return

    for key, desc in result.added.items():
        click.echo(f"  [added]   {key}: {desc}")
    for key, desc in result.updated.items():
        click.echo(f"  [updated] {key}: {desc}")
    for key in result.removed:
        click.echo(f"  [removed] {key}")
    click.echo(f"\n{result.total_changes} annotation change(s) applied to {project}/{environment}.")
