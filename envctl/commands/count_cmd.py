import json
import click
from envctl.count import count_env, CountError
from envctl.env_store import read_env
from envctl.config import load_config, get_envs_dir


def _read(project: str, environment: str) -> dict[str, str]:
    cfg = load_config()
    envs_dir = get_envs_dir(cfg)
    return read_env(project, environment, envs_dir)


@click.command("count")
@click.argument("project")
@click.argument("environment")
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]), show_default=True)
def count_cmd(project: str, environment: str, fmt: str) -> None:
    """Count keys in a project/environment."""
    try:
        result = count_env(project, environment, _read)
    except CountError as exc:
        raise click.ClickException(str(exc))

    if fmt == "json":
        click.echo(json.dumps(result.to_dict(), indent=2))
    else:
        click.echo(f"Project:     {result.project}")
        click.echo(f"Environment: {result.environment}")
        click.echo(f"Total keys:  {result.total}")
        click.echo(f"Non-empty:   {result.non_empty}")
        click.echo(f"Empty:       {result.empty}")
