"""CLI command: envctl resolve — resolve cross-environment variable references."""
from __future__ import annotations

import json

import click

from envctl.config import load_config, get_envs_dir
from envctl.env_store import read_env
from envctl.resolve import resolve_env, ResolveError


@click.command("resolve")
@click.argument("project")
@click.argument("environment")
@click.option("--strict", is_flag=True, default=False, help="Fail on unresolved references.")
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["dotenv", "json"]),
    default="dotenv",
    show_default=True,
    help="Output format.",
)
def resolve_cmd(project: str, environment: str, strict: bool, fmt: str) -> None:
    """Resolve cross-environment ${ENV:KEY} references for PROJECT/ENVIRONMENT."""
    cfg = load_config()
    envs_dir = get_envs_dir(cfg)

    def _read(proj: str, env: str) -> dict[str, str]:
        return read_env(envs_dir, proj, env)

    try:
        result = resolve_env(project, environment, _read, strict=strict)
    except ResolveError as exc:
        raise click.ClickException(str(exc)) from exc

    if result.total_unresolved:
        for key, ref in result.unresolved:
            click.echo(click.style(f"  ! unresolved: {key} -> {ref}", fg="yellow"), err=True)

    if fmt == "json":
        click.echo(json.dumps(result.resolved, indent=2))
    else:
        for k, v in result.resolved.items():
            click.echo(f"{k}={v}")

    click.echo(
        click.style(
            f"Resolved {result.total_substitutions} reference(s), "
            f"{result.total_unresolved} unresolved.",
            fg="green" if result.total_unresolved == 0 else "yellow",
        ),
        err=True,
    )
