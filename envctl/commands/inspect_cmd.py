"""CLI command: envctl inspect <project> <environment>"""
from __future__ import annotations

import json

import click

from envctl.config import get_envs_dir, load_config
from envctl.env_store import read_env
from envctl.inspect import InspectError, inspect_env


@click.command("inspect")
@click.argument("project")
@click.argument("environment")
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text", show_default=True)
@click.option("--show-values", is_flag=True, default=False, help="Print actual values (hidden by default).")
def inspect_cmd(project: str, environment: str, fmt: str, show_values: bool) -> None:
    """Inspect keys and metadata for PROJECT / ENVIRONMENT."""
    config = load_config()
    envs_dir = get_envs_dir(config)

    def _read(p: str, e: str):
        return read_env(p, e, envs_dir=envs_dir)

    try:
        result = inspect_env(project, environment, _read)
    except InspectError as exc:
        raise click.ClickException(str(exc)) from exc

    if fmt == "json":
        data = result.to_dict()
        if not show_values:
            for kd in data["keys"]:
                kd["value"] = "***"
        click.echo(json.dumps(data, indent=2))
        return

    click.echo(f"Project     : {result.project}")
    click.echo(f"Environment : {result.environment}")
    click.echo(f"Total keys  : {result.total_keys}")
    click.echo(f"Empty keys  : {result.empty_keys}")
    click.echo(f"Placeholders: {result.placeholder_keys}")
    if result.keys:
        click.echo("")
        click.echo(f"  {'KEY':<30} {'EMPTY':>5}  {'PLACEHOLDER':>11}  {'LEN':>5}")
        click.echo("  " + "-" * 56)
        for kd in result.keys:
            val_col = kd.value if show_values else "***"
            click.echo(
                f"  {kd.key:<30} {'yes' if kd.is_empty else 'no':>5}  "
                f"{'yes' if kd.has_placeholder else 'no':>11}  {kd.length:>5}  {val_col}"
            )
