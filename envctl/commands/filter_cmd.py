import json
import click
from envctl.filter import filter_env, FilterError
from envctl.config import load_config, get_envs_dir
from envctl.env_store import read_env as _store_read_env


@click.command("filter")
@click.argument("project")
@click.argument("environment")
@click.option("--prefix", default=None, help="Only keys starting with this prefix.")
@click.option("--suffix", default=None, help="Only keys ending with this suffix.")
@click.option("--contains", default=None, help="Only keys containing this substring.")
@click.option("--value-contains", default=None, help="Only keys whose value contains this substring.")
@click.option("--invert", is_flag=True, default=False, help="Invert the filter match.")
@click.option("--format", "fmt", type=click.Choice(["dotenv", "json"]), default="dotenv")
def filter_cmd(project, environment, prefix, suffix, contains, value_contains, invert, fmt):
    """Filter keys in an environment by key/value patterns."""
    cfg = load_config()
    envs_dir = get_envs_dir(cfg)

    # Warn if no filter options were provided — result will include all keys.
    if not any([prefix, suffix, contains, value_contains]):
        click.echo("Warning: no filter options specified; all keys will be returned.", err=True)

    def read_env(p, e):
        return _store_read_env(p, e, envs_dir=envs_dir)

    try:
        result = filter_env(
            project=project,
            environment=environment,
            read_env=read_env,
            prefix=prefix,
            suffix=suffix,
            contains=contains,
            value_contains=value_contains,
            invert=invert,
        )
    except FilterError as e:
        raise click.ClickException(str(e))

    if not result.matched:
        click.echo("No keys matched the filter.")
        return

    if fmt == "json":
        click.echo(json.dumps(result.to_dict(), indent=2))
    else:
        for key, value in sorted(result.matched.items()):
            click.echo(f"{key}={value}")
        click.echo(f"\n# {result.total_matched()} of {result.total_scanned} keys matched.", err=True)
