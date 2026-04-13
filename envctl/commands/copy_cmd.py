"""CLI command for copying environment variables between environments."""

import click
from envctl.copy import copy_env, CopyError


@click.command(name="copy")
@click.argument("src_project")
@click.argument("src_env")
@click.argument("dst_project")
@click.argument("dst_env")
@click.option(
    "--keys",
    "-k",
    multiple=True,
    help="Specific keys to copy. Repeatable. Copies all keys if omitted.",
)
@click.option(
    "--overwrite",
    is_flag=True,
    default=False,
    help="Overwrite existing keys in the destination environment.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Preview which keys would be copied without making any changes.",
)
def copy_cmd(
    src_project: str,
    src_env: str,
    dst_project: str,
    dst_env: str,
    keys: tuple[str, ...],
    overwrite: bool,
    dry_run: bool,
) -> None:
    """Copy env vars from SRC_PROJECT/SRC_ENV to DST_PROJECT/DST_ENV.

    By default, existing keys in the destination are preserved.
    Use --overwrite to replace them.
    """
    try:
        copied = copy_env(
            src_project=src_project,
            src_env=src_env,
            dst_project=dst_project,
            dst_env=dst_env,
            keys=list(keys) if keys else None,
            overwrite=overwrite,
            dry_run=dry_run,
        )
    except CopyError as exc:
        raise click.ClickException(str(exc)) from exc

    if not copied:
        click.echo("Nothing to copy — all keys already exist in the destination.")
        return

    action = "Would copy" if dry_run else "Copied"
    click.echo(
        f"{action} {len(copied)} key(s) from "
        f"{src_project}/{src_env} \u2192 {dst_project}/{dst_env}:"
    )
    for key in sorted(copied):
        click.echo(f"  {key}")

    if dry_run:
        click.echo("(Dry run — no changes were made.)")
