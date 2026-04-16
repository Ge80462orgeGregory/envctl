import click
import json
from envctl.prefix import add_prefix, strip_prefix, PrefixError
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


@click.group("prefix")
def prefix_cmd():
    """Add or strip key prefixes in an environment."""


@prefix_cmd.command("add")
@click.argument("project")
@click.argument("environment")
@click.argument("prefix")
@click.option("--overwrite", is_flag=True, default=False, help="Overwrite if prefixed key already exists.")
@click.option("--json", "as_json", is_flag=True, default=False)
def prefix_add(project, environment, prefix, overwrite, as_json):
    """Add PREFIX to all keys in PROJECT/ENVIRONMENT."""
    try:
        result = add_prefix(project, environment, prefix, _read, _write, overwrite=overwrite)
    except PrefixError as e:
        raise click.ClickException(str(e))

    if as_json:
        click.echo(json.dumps(result.to_dict(), indent=2))
    else:
        if result.total_changed == 0:
            click.echo("No keys were updated.")
        else:
            click.echo(f"Added prefix '{prefix}' to {result.total_changed} key(s).")
            for k in result.changed:
                click.echo(f"  {k} -> {prefix}{k}")


@prefix_cmd.command("strip")
@click.argument("project")
@click.argument("environment")
@click.argument("prefix")
@click.option("--json", "as_json", is_flag=True, default=False)
def prefix_strip(project, environment, prefix, as_json):
    """Strip PREFIX from all matching keys in PROJECT/ENVIRONMENT."""
    try:
        result = strip_prefix(project, environment, prefix, _read, _write)
    except PrefixError as e:
        raise click.ClickException(str(e))

    if as_json:
        click.echo(json.dumps(result.to_dict(), indent=2))
    else:
        if result.total_changed == 0:
            click.echo("No keys matched the prefix.")
        else:
            click.echo(f"Stripped prefix '{prefix}' from {result.total_changed} key(s).")
            for k in result.changed:
                click.echo(f"  {k} -> {k[len(prefix):]}")
