"""CLI command: envctl flatten."""

from __future__ import annotations

import json

import click

from envctl.config import load_config, get_envs_dir
from envctl.env_store import list_environments, read_env
from envctl.flatten import FlattenError, flatten_envs


@click.command("flatten")
@click.argument("project")
@click.argument("environments", nargs=-1, required=True)
@click.option(
    "--priority",
    default=None,
    help="Environment whose values win on conflict.",
)
@click.option(
    "--skip-conflicts",
    is_flag=True,
    default=False,
    help="Omit conflicting keys from output entirely.",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["dotenv", "json"]),
    default="dotenv",
    show_default=True,
    help="Output format.",
)
def flatten_cmd(
    project: str,
    environments: tuple[str, ...],
    priority: str | None,
    skip_conflicts: bool,
    output_format: str,
) -> None:
    """Flatten ENVIRONMENTS of PROJECT into a single variable set."""
    cfg = load_config()
    envs_dir = get_envs_dir(cfg)

    def _read(proj: str, env: str) -> dict[str, str]:
        return read_env(proj, env, envs_dir=envs_dir)

    def _list(proj: str) -> list[str]:
        return list_environments(proj, envs_dir=envs_dir)

    try:
        result = flatten_envs(
            project=project,
            environments=list(environments),
            read_env=_read,
            list_environments=_list,
            priority=priority,
            skip_conflicts=skip_conflicts,
        )
    except FlattenError as exc:
        raise click.ClickException(str(exc)) from exc

    if result.total_conflicts:
        conflict_keys = ", ".join(result.conflicts.keys())
        click.echo(
            f"Warning: {result.total_conflicts} conflict(s) detected: {conflict_keys}",
            err=True,
        )

    if output_format == "json":
        click.echo(json.dumps(result.merged, indent=2))
    else:
        for key, value in sorted(result.merged.items()):
            click.echo(f'{key}="{value}"')
