"""CLI command: align — pad or truncate env values to a fixed width."""

import json
import click
from envctl.align import align_env, AlignError


@click.command("align")
@click.argument("project")
@click.argument("environment")
@click.option("--width", "-w", required=True, type=int, help="Target value width.")
@click.option("--fill", default=" ", show_default=True, help="Fill character for padding.")
@click.option("--truncate", is_flag=True, default=False, help="Truncate values longer than width.")
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text", show_default=True)
def align_cmd(project, environment, width, fill, truncate, fmt):
    """Pad or truncate all values in PROJECT/ENVIRONMENT to a fixed WIDTH."""
    try:
        result = align_env(
            project=project,
            environment=environment,
            width=width,
            fill_char=fill,
            truncate=truncate,
        )
    except AlignError as exc:
        raise click.ClickException(str(exc))

    if fmt == "json":
        click.echo(json.dumps(result.to_dict(), indent=2))
        return

    if result.total_changed == 0:
        click.echo("Nothing to align — all values already match the target width.")
        return

    click.echo(f"Aligned {result.total_changed} value(s) in {project}/{environment} to width {width}.")
    for key, new_val in result.aligned.items():
        old_val = result.original[key]
        if old_val != new_val:
            click.echo(f"  {key}: {repr(old_val)} -> {repr(new_val)}")
