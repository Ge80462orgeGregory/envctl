import json
import click
from envctl.required import check_required, RequiredError
from envctl.env_store import read_env
from envctl.config import load_config, get_envs_dir


@click.command("required")
@click.argument("project")
@click.argument("environment")
@click.argument("keys", nargs=-1, required=True)
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
def required_cmd(ctx, project, environment, keys, fmt):
    """Check that required keys exist and are non-empty in an environment."""
    config = load_config()
    envs_dir = get_envs_dir(config)

    def _read(p, e):
        return read_env(envs_dir, p, e)

    try:
        result = check_required(project, environment, list(keys), _read)
    except RequiredError as exc:
        click.echo(f"Error: {exc}", err=True)
        ctx.exit(1)
        return

    if fmt == "json":
        click.echo(json.dumps(result.to_dict(), indent=2))
        return

    if result.satisfied:
        click.echo(f"All {len(result.required)} required key(s) are present.")
    else:
        click.echo(f"Missing {len(result.missing)} required key(s):")
        for k in result.missing:
            click.echo(f"  - {k}")
        if result.present:
            click.echo(f"Present ({len(result.present)}): {', '.join(result.present)}")
        ctx.exit(1)
