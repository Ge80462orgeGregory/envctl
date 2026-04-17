"""CLI command for lowercasing env values."""
import json
import click
from envctl.lowercase import lowercase_env, LowercaseError
from envctl.env_store import read_env, write_env
from envctl.config import load_config, get_envs_dir


def _read(project, environment):
    cfg = load_config()
    envs_dir = get_envs_dir(cfg)
    return read_env(envs_dir, project, environment)


def _write(project, environment, data):
    cfg = load_config()
    envs_dir = get_envs_dir(cfg)
    write_env(envs_dir, project, environment, data)


@click.command("lowercase")
@click.argument("project")
@click.argument("environment")
@click.option("--key", "keys", multiple=True, help="Restrict to specific keys")
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]), show_default=True)
def lowercase_cmd(project, environment, keys, fmt):
    """Lowercase values in an environment."""
    try:
        result = lowercase_env(
            project=project,
            environment=environment,
            read_env=_read,
            write_env=_write,
            keys=list(keys) if keys else None,
        )
    except LowercaseError as e:
        raise click.ClickException(str(e))

    if fmt == "json":
        click.echo(json.dumps(result.to_dict(), indent=2))
        return

    if result.total_changed == 0:
        click.echo("Nothing to lowercase.")
        return

    click.echo(f"Lowercased {result.total_changed} value(s) in {project}/{environment}:")
    for k, v in result.changes.items():
        click.echo(f"  {k} = {v}")
