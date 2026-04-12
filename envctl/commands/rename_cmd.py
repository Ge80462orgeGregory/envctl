"""CLI command for renaming an environment within a project."""

import click
from envctl.rename import rename_env, RenameError
from envctl.config import load_config, get_envs_dir


@click.command("rename")
@click.argument("project")
@click.argument("src_env")
@click.argument("dst_env")
@click.option(
    "--overwrite",
    is_flag=True,
    default=False,
    help="Overwrite destination environment if it already exists.",
)
def rename_cmd(project: str, src_env: str, dst_env: str, overwrite: bool) -> None:
    """Rename SRC_ENV to DST_ENV for PROJECT.

    The source environment file is removed after a successful rename.
    """
    config = load_config()
    envs_dir = get_envs_dir(config)

    try:
        result = rename_env(
            project=project,
            src_env=src_env,
            dst_env=dst_env,
            envs_dir=envs_dir,
            overwrite=overwrite,
        )
    except RenameError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(
        f"Renamed '{result['src']}' -> '{result['dst']}' "
        f"for project '{result['project']}' "
        f"({result['keys_moved']} key(s) moved)."
    )
