"""CLI command: envctl import <project> <environment> <file>"""

from __future__ import annotations

from pathlib import Path

import click

from envctl.import_ import ImportError, import_env  # noqa: A004


@click.command("import")
@click.argument("project")
@click.argument("environment")
@click.argument("file", type=click.Path(exists=False, dir_okay=False))
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["dotenv", "json"], case_sensitive=False),
    default="dotenv",
    show_default=True,
    help="Format of the source file.",
)
@click.option(
    "--overwrite",
    is_flag=True,
    default=False,
    help="Overwrite existing keys that conflict.",
)
@click.option(
    "--prefix",
    default=None,
    metavar="PREFIX",
    help="Prepend PREFIX to every imported key.",
)
def import_cmd(
    project: str,
    environment: str,
    file: str,
    fmt: str,
    overwrite: bool,
    prefix: str | None,
) -> None:
    """Import environment variables from FILE into PROJECT/ENVIRONMENT."""
    source = Path(file)
    try:
        written = import_env(
            project,
            environment,
            source,
            fmt=fmt,
            overwrite=overwrite,
            prefix=prefix,
        )
    except ImportError as exc:
        raise click.ClickException(str(exc)) from exc

    if not written:
        click.echo("Nothing to import (no new or changed keys).")
        return

    click.echo(
        f"Imported {len(written)} key(s) into '{project}/{environment}':"
    )
    for key in sorted(written):
        click.echo(f"  {key}")
