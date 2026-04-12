"""CLI command for syncing environment variables between environments."""

import click
from envctl.sync import sync_envs, SyncConflict
from envctl.config import load_config, get_envs_dir


@click.command(name="sync")
@click.argument("project")
@click.argument("source_env")
@click.argument("target_env")
@click.option(
    "--overwrite",
    is_flag=True,
    default=False,
    help="Overwrite conflicting keys in the target environment.",
)
@click.option(
    "--key",
    "keys",
    multiple=True,
    help="Specific key(s) to sync. Can be specified multiple times.",
)
def sync_cmd(project: str, source_env: str, target_env: str, overwrite: bool, keys: tuple):
    """Sync environment variables from SOURCE_ENV to TARGET_ENV for PROJECT."""
    config = load_config()
    envs_dir = get_envs_dir(config)

    selected_keys = list(keys) if keys else None

    try:
        result = sync_envs(
            project=project,
            source_env=source_env,
            target_env=target_env,
            overwrite=overwrite,
            keys=selected_keys,
        )
    except SyncConflict as e:
        click.echo(click.style(f"Error: {e}", fg="red"), err=True)
        raise click.Abort()

    added = result["added"]
    updated = result["updated"]
    skipped = result["skipped"]

    if added:
        click.echo(click.style(f"Added ({len(added)}):", fg="green"))
        for key in added:
            click.echo(f"  + {key}")

    if updated:
        click.echo(click.style(f"Updated ({len(updated)}):", fg="yellow"))
        for key in updated:
            click.echo(f"  ~ {key}")

    if skipped:
        click.echo(click.style(f"Skipped ({len(skipped)}):", fg="cyan"))
        for key in skipped:
            click.echo(f"  = {key}")

    if not added and not updated:
        click.echo("Nothing to sync — target is already up to date.")
    else:
        click.echo(
            click.style(
                f"\nSync complete: {len(added)} added, {len(updated)} updated.",
                fg="green",
            )
        )
