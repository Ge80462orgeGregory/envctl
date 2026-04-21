import click
import json
from envctl.mask import mask_env, MaskError
from envctl.env_store import read_env, write_env
from envctl.config import load_config, get_envs_dir


def _read(project, environment, envs_dir):
    return read_env(project, environment, envs_dir)


def _write(project, environment, data, envs_dir):
    write_env(project, environment, data, envs_dir)


@click.command("mask")
@click.argument("project")
@click.argument("environment")
@click.option("--dry-run", is_flag=True, default=False, help="Preview masked output without writing.")
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text", show_default=True)
def mask_cmd(project, environment, dry_run, fmt):
    """Mask sensitive values in a project environment."""
    config = load_config()
    envs_dir = get_envs_dir(config)

    try:
        env = _read(project, environment, envs_dir)
        result = mask_env(project, environment, env)

        if not dry_run:
            _write(project, environment, result.masked, envs_dir)

        if fmt == "json":
            click.echo(json.dumps({
                "project": project,
                "environment": environment,
                "total_masked": result.total_masked,
                "dry_run": dry_run,
                "masked": result.masked,
            }, indent=2))
        else:
            if result.total_masked == 0:
                click.echo("No sensitive keys found.")
            else:
                label = "(dry run) " if dry_run else ""
                click.echo(f"{label}Masked {result.total_masked} key(s) in [{project}:{environment}]")
                for key in result.masked_keys:
                    click.echo(f"  - {key}")
    except MaskError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
