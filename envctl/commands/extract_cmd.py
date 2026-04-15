"""CLI command for extracting keys from one environment to another."""

import json
import click
from envctl.extract import extract_env, ExtractError
from envctl.env_store import read_env, write_env
from envctl.config import load_config, get_envs_dir


@click.command("extract")
@click.argument("project")
@click.argument("source_env")
@click.argument("target_env")
@click.option("-k", "--key", "keys", multiple=True, required=True, help="Key(s) to extract.")
@click.option("--overwrite", is_flag=True, default=False, help="Overwrite existing keys in target.")
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text", show_default=True)
def extract_cmd(project, source_env, target_env, keys, overwrite, fmt):
    """Extract specific keys from SOURCE_ENV into TARGET_ENV."""
    config = load_config()
    envs_dir = get_envs_dir(config)

    def _read(proj, env):
        return read_env(envs_dir, proj, env)

    def _write(proj, env, data):
        write_env(envs_dir, proj, env, data)

    try:
        result = extract_env(
            project=project,
            source_env=source_env,
            target_env=target_env,
            keys=list(keys),
            read=_read,
            write=_write,
            overwrite=overwrite,
        )
    except ExtractError as exc:
        raise click.ClickException(str(exc))

    if fmt == "json":
        click.echo(json.dumps(result.to_dict(), indent=2))
        return

    if result.total_extracted == 0:
        click.echo("Nothing extracted.")
    else:
        click.echo(f"Extracted {result.total_extracted} key(s) from '{source_env}' into '{target_env}':")
        for key in result.extracted:
            click.echo(f"  + {key}")

    if result.skipped:
        click.echo(f"Skipped {len(result.skipped)} key(s): {', '.join(result.skipped)}")
