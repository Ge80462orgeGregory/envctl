"""CLI command for applying default values to an environment."""

import json
import click
from envctl.defaults import apply_defaults, DefaultsError
from envctl.env_store import read_env, write_env
from envctl.config import load_config, get_envs_dir


@click.command("defaults")
@click.argument("project")
@click.argument("environment")
@click.option("--set", "pairs", multiple=True, metavar="KEY=VALUE",
              help="Default key=value pair (repeatable).")
@click.option("--overwrite", is_flag=True, default=False,
              help="Overwrite existing keys with defaults.")
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
def defaults_cmd(project, environment, pairs, overwrite, fmt):
    """Apply default values for missing keys in PROJECT/ENVIRONMENT."""
    if not pairs:
        raise click.UsageError("Provide at least one --set KEY=VALUE pair.")

    defaults = {}
    for pair in pairs:
        if "=" not in pair:
            raise click.UsageError(f"Invalid format '{pair}', expected KEY=VALUE.")
        k, v = pair.split("=", 1)
        defaults[k.strip()] = v.strip()

    cfg = load_config()
    envs_dir = get_envs_dir(cfg)

    def _read(p, e):
        return read_env(p, e, envs_dir)

    def _write(p, e, data):
        write_env(p, e, data, envs_dir)

    try:
        result = apply_defaults(project, environment, defaults, _read, _write, overwrite)
    except DefaultsError as exc:
        raise click.ClickException(str(exc))

    if fmt == "json":
        click.echo(json.dumps(result.to_dict(), indent=2))
    else:
        if result.total_applied == 0:
            click.echo("No defaults applied.")
        else:
            for key, value in result.applied.items():
                click.echo(f"  set {key}={value}")
            click.echo(f"Applied {result.total_applied} default(s).")
        if result.skipped:
            click.echo(f"Skipped (already set): {', '.join(result.skipped)}")
