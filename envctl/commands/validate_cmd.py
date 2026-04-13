"""CLI command for validating an environment variable set."""
import json
import sys

import click

from envctl.config import get_envs_dir, load_config
from envctl.env_store import read_env
from envctl.validate import ValidateError, validate_env


@click.command("validate")
@click.argument("project")
@click.argument("environment")
@click.option(
    "--require",
    "required_keys",
    multiple=True,
    metavar="KEY",
    help="Assert that KEY is present (repeatable).",
)
@click.option("--json", "as_json", is_flag=True, help="Output results as JSON.")
@click.pass_context
def validate_cmd(ctx: click.Context, project: str, environment: str, required_keys: tuple, as_json: bool) -> None:
    """Validate environment variables for PROJECT / ENVIRONMENT."""
    cfg = load_config()
    envs_dir = get_envs_dir(cfg)

    try:
        variables = read_env(envs_dir, project, environment)
    except Exception as exc:  # pragma: no cover
        raise click.ClickException(str(exc)) from exc

    result = validate_env(
        project=project,
        environment=environment,
        variables=variables,
        required_keys=list(required_keys) or None,
    )

    if as_json:
        payload = {
            "project": result.project,
            "environment": result.environment,
            "valid": result.valid,
            "issues": [
                {"key": i.key, "message": i.message, "severity": i.severity}
                for i in result.issues
            ],
        }
        click.echo(json.dumps(payload, indent=2))
    else:
        if not result.issues:
            click.secho(f"✔  {project}/{environment} is valid.", fg="green")
        else:
            for issue in result.errors:
                click.secho(f"[error]   {issue.key}: {issue.message}", fg="red")
            for issue in result.warnings:
                click.secho(f"[warning] {issue.key}: {issue.message}", fg="yellow")

    if not result.valid:
        sys.exit(1)
