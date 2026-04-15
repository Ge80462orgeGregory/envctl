"""CLI command: envctl prune."""

import json
import sys

import click

from envctl.config import get_envs_dir, load_config
from envctl.env_store import read_env, write_env
from envctl.prune import PruneError, prune_env


@click.command("prune")
@click.argument("project")
@click.argument("environment")
@click.option(
    "--ref",
    "reference_environment",
    required=True,
    help="Reference environment whose keys define the allowed set.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Preview removals without modifying the environment.",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    default=False,
    help="Output result as JSON.",
)
def prune_cmd(
    project: str,
    environment: str,
    reference_environment: str,
    dry_run: bool,
    output_json: bool,
) -> None:
    """Remove keys from ENVIRONMENT that are absent in the reference environment."""
    config = load_config()
    envs_dir = get_envs_dir(config)

    def _read(proj: str, env: str):
        return read_env(proj, env, envs_dir=envs_dir)

    def _write(proj: str, env: str, variables: dict):
        write_env(proj, env, variables, envs_dir=envs_dir)

    try:
        result = prune_env(
            project=project,
            environment=environment,
            reference_environment=reference_environment,
            read_env=_read,
            write_env=_write,
            dry_run=dry_run,
        )
    except PruneError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    if output_json:
        click.echo(json.dumps(result.to_dict(), indent=2))
        return

    prefix = "[dry-run] " if dry_run else ""
    if result.total_removed == 0:
        click.echo(f"{prefix}Nothing to prune in '{project}/{environment}'.")
    else:
        click.echo(
            f"{prefix}Pruned {result.total_removed} key(s) from "
            f"'{project}/{environment}' (ref: {reference_environment}):"
        )
        for key in sorted(result.removed_keys):
            click.echo(f"  - {key}")
