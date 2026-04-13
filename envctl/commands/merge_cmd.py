"""CLI command: envctl merge"""
from __future__ import annotations

import click

from envctl.merge import MergeError, merge_envs


@click.command("merge")
@click.argument("project")
@click.argument("source_a")
@click.argument("source_b")
@click.argument("target")
@click.option(
    "--overwrite",
    is_flag=True,
    default=False,
    help="Overwrite keys that already exist in the target environment.",
)
@click.option(
    "--key",
    "keys",
    multiple=True,
    metavar="KEY",
    help="Merge only these specific keys (repeatable).",
)
def merge_cmd(
    project: str,
    source_a: str,
    source_b: str,
    target: str,
    overwrite: bool,
    keys: tuple,
) -> None:
    """Merge SOURCE_A and SOURCE_B into TARGET for PROJECT.

    Keys present in both sources use the value from SOURCE_B.
    """
    try:
        result = merge_envs(
            project,
            source_a,
            source_b,
            target,
            overwrite=overwrite,
            keys=list(keys) if keys else None,
        )
    except MergeError as exc:
        raise click.ClickException(str(exc)) from exc

    if result.total_changes == 0 and not result.skipped:
        click.echo("Nothing to merge.")
        return

    if result.added:
        click.echo(f"Added {len(result.added)} key(s): {', '.join(sorted(result.added))}")
    if result.overwritten:
        click.echo(
            f"Overwrote {len(result.overwritten)} key(s): {', '.join(sorted(result.overwritten))}"
        )
    if result.skipped:
        click.echo(
            f"Skipped {len(result.skipped)} key(s) (use --overwrite to update existing)."
        )

    click.echo(
        f"Merge complete: {result.total_changes} change(s) written to "
        f"'{project}/{target}'."
    )
