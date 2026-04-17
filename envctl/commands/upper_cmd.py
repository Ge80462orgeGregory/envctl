import click
import json
from envctl.upper import upper_env, UpperError
from envctl.env_store import read_env, write_env
from envctl.config import load_config, get_envs_dir


@click.command("upper")
@click.argument("project")
@click.argument("environment")
@click.option("--keys", "-k", multiple=True, help="Specific keys to uppercase (default: all)")
@click.option("--dry-run", is_flag=True, default=False, help="Preview changes without writing")
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
def upper_cmd(project, environment, keys, dry_run, fmt):
    """Convert environment variable values to uppercase."""
    config = load_config()
    envs_dir = get_envs_dir(config)

    def _read(p, e):
        return read_env(envs_dir, p, e)

    def _write(p, e, data):
        write_env(envs_dir, p, e, data)

    try:
        result = upper_env(
            project=project,
            environment=environment,
            read_env=_read,
            write_env=_write,
            keys=list(keys) if keys else None,
            dry_run=dry_run,
        )
    except UpperError as e:
        raise click.ClickException(str(e))

    if fmt == "json":
        click.echo(json.dumps(result.to_dict(), indent=2))
        return

    if result.total_changed == 0:
        click.echo("No values changed.")
    else:
        prefix = "[dry-run] " if dry_run else ""
        click.echo(f"{prefix}Uppercased {result.total_changed} key(s) in '{project}/{environment}':")
        for key in result.changed_keys:
            click.echo(f"  {key}")
