"""CLI command: envctl unique — show keys unique to one environment."""
from __future__ import annotations
import json
import click
from envctl.unique import find_unique, UniqueError
from envctl.env_store import read_env, list_environments
from envctl.config import load_config, get_envs_dir


def _read(project: str, env: str) -> dict:
    cfg = load_config()
    envs_dir = get_envs_dir(cfg)
    return read_env(envs_dir, project, env)


def _list_envs(project: str):
    cfg = load_config()
    envs_dir = get_envs_dir(cfg)
    return list_environments(envs_dir, project)


@click.command("unique")
@click.argument("project")
@click.argument("source_env")
@click.argument("compared_envs", nargs=-1)
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]), show_default=True)
def unique_cmd(project: str, source_env: str, compared_envs, fmt: str):
    """Show keys in SOURCE_ENV that do not appear in any COMPARED_ENVS.

    If COMPARED_ENVS are omitted, all other environments in the project are used.
    """
    try:
        result = find_unique(
            project=project,
            source_env=source_env,
            compared_envs=list(compared_envs),
            read_fn=_read,
            list_envs_fn=_list_envs,
        )
    except UniqueError as exc:
        raise click.ClickException(str(exc))

    if fmt == "json":
        click.echo(json.dumps(result.to_dict(), indent=2))
        return

    if result.total_unique == 0:
        click.echo(
            f"No unique keys found in '{source_env}' compared to: "
            + ", ".join(result.compared_envs)
        )
        return

    click.echo(
        f"Keys unique to '{source_env}' (not in "
        + ", ".join(result.compared_envs)
        + f")  [{result.total_unique} key(s)]"
    )
    for key, value in sorted(result.unique_keys.items()):
        click.echo(f"  {key}={value}")
