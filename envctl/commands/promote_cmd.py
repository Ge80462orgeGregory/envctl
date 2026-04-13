"""CLI command for promoting environment variables between environments."""

import click

from envctl.promote import PromoteError, promote_env


@click.command("promote")
@click.argument("project")
@click.argument("source_env")
@click.argument("target_env")
@click.option("--keys", "-k", multiple=True, help="Specific keys to promote (default: all).")
@click.option("--overwrite", "-o", is_flag=True, default=False, help="Overwrite conflicting keys in target.")
def promote_cmd(project, source_env, target_env, keys, overwrite):
    """Promote variables from SOURCE_ENV to TARGET_ENV in PROJECT.

    Example:
        envctl promote myapp staging production
        envctl promote myapp staging production -k API_KEY -k DB_URL --overwrite
    """
    try:
        result = promote_env(
            project=project,
            source_env=source_env,
            target_env=target_env,
            keys=list(keys) if keys else None,
            overwrite=overwrite,
        )
    except PromoteError as exc:
        raise click.ClickException(str(exc)) from exc

    total = len(result.promoted) + len(result.overwritten) + len(result.skipped)

    if total == 0:
        click.echo("Nothing to promote.")
        return

    if result.promoted:
        click.echo(f"Promoted {len(result.promoted)} new key(s) to '{target_env}':")
        for key in sorted(result.promoted):
            click.echo(f"  + {key}")

    if result.overwritten:
        click.echo(f"Overwritten {len(result.overwritten)} key(s) in '{target_env}':")
        for key in sorted(result.overwritten):
            click.echo(f"  ~ {key}")

    if result.skipped:
        click.echo(f"Skipped {len(result.skipped)} key(s) (already exist or identical):")
        for key in sorted(result.skipped):
            click.echo(f"  = {key}")

    click.echo(f"\nPromotion from '{source_env}' to '{target_env}' complete.")
