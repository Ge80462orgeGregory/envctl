import json
import click
from envctl.squash import squash_envs, SquashError
from envctl.env_store import read_env, write_env
from envctl.config import load_config, get_envs_dir


@click.command("squash")
@click.argument("project")
@click.argument("sources", nargs=-1, required=True)
@click.option("--target", required=True, help="Target environment name to write merged result.")
@click.option("--overwrite", is_flag=True, default=False, help="Use last-write wins on conflicts.")
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
def squash_cmd(project, sources, target, overwrite, fmt):
    """Squash multiple environments into a single target environment."""
    config = load_config()
    envs_dir = get_envs_dir(config)

    def _read(p, e):
        return read_env(envs_dir, p, e)

    def _write(p, e, data):
        return write_env(envs_dir, p, e, data)

    try:
        result = squash_envs(
            project=project,
            sources=list(sources),
            target=target,
            read_env=_read,
            write_env=_write,
            overwrite=overwrite,
        )
    except SquashError as e:
        raise click.ClickException(str(e))

    if fmt == "json":
        click.echo(json.dumps(result.to_dict(), indent=2))
    else:
        click.echo(f"Squashed {len(result.sources)} environments into '{result.target}'.")
        click.echo(f"  Total keys : {result.total_keys}")
        click.echo(f"  Conflicts  : {result.total_conflicts}")
        if result.conflicts:
            for key, vals in result.conflicts.items():
                click.echo(f"    {key}: {vals}")
