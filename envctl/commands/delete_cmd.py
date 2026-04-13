"""CLI command for deleting an environment or specific keys."""

import click

from envctl.delete import DeleteError, delete_env_or_keys


@click.command("delete")
@click.argument("project")
@click.argument("environment")
@click.option(
    "-k",
    "--key",
    "keys",
    multiple=True,
    metavar="KEY",
    help="Key(s) to delete. Omit to delete the entire environment.",
)
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    default=False,
    help="Skip confirmation prompt.",
)
def delete_cmd(project: str, environment: str, keys: tuple, yes: bool) -> None:
    """Delete an environment or specific keys within it.

    \b
    Examples:
      envctl delete myapp staging            # delete entire staging env
      envctl delete myapp staging -k DB_URL  # delete only DB_URL key
    """
    if not yes:
        if keys:
            target = f"keys {', '.join(keys)} from {project}/{environment}"
        else:
            target = f"environment {project}/{environment}"
        click.confirm(f"Are you sure you want to delete {target}?", abort=True)

    try:
        result = delete_env_or_keys(
            project,
            environment,
            keys=list(keys) if keys else None,
        )
    except DeleteError as exc:
        raise click.ClickException(str(exc)) from exc

    if result["deleted_env"]:
        click.echo(f"Deleted environment '{environment}' from project '{project}'.")
    else:
        for key in result["removed_keys"]:
            click.echo(f"Removed key '{key}' from '{project}/{environment}'.")
