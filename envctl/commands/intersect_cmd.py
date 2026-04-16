"""CLI command: envctl intersect"""
import json
import click
from envctl.intersect import intersect_envs, IntersectError
from envctl.env_store import read_env
from envctl.config import load_config, get_envs_dir


@click.command("intersect")
@click.argument("project")
@click.argument("source_env")
@click.argument("target_env")
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]), show_default=True)
def intersect_cmd(project: str, source_env: str, target_env: str, fmt: str) -> None:
    """Show keys common to SOURCE_ENV and TARGET_ENV in PROJECT."""
    cfg = load_config()
    envs_dir = get_envs_dir(cfg)

    def _read(p, e):
        return read_env(envs_dir, p, e)

    try:
        result = intersect_envs(project, source_env, target_env, _read)
    except IntersectError as exc:
        raise click.ClickException(str(exc))

    if fmt == "json":
        click.echo(json.dumps(result.to_dict(), indent=2))
        return

    if not result.common_keys:
        click.echo(f"No common keys between '{source_env}' and '{target_env}'.")
        return

    click.echo(f"Common keys ({result.total}) between '{source_env}' and '{target_env}':")
    for key in result.common_keys:
        tag = "=" if key in result.common_with_same_value else "~"
        click.echo(f"  [{tag}] {key}")
    click.echo(f"\nSame value: {len(result.common_with_same_value)}  Diff value: {len(result.common_with_diff_value)}")
