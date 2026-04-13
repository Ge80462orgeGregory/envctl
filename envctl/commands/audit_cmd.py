"""CLI command for viewing the envctl audit log."""

import json
import click

from envctl.audit import read_log, format_log, AuditError
from envctl.config import load_config, get_envs_dir


@click.command("audit")
@click.option("--project", "-p", default=None, help="Filter by project name.")
@click.option("--env", "-e", "environment", default=None, help="Filter by environment name.")
@click.option("--format", "output_format", type=click.Choice(["text", "json"]), default="text", show_default=True, help="Output format.")
@click.option("--tail", "-n", default=None, type=int, help="Show only the last N entries.")
def audit_cmd(project, environment, output_format, tail):
    """Display the audit log of environment variable changes."""
    config = load_config()
    envs_dir = get_envs_dir(config)

    try:
        entries = read_log(envs_dir=envs_dir, project=project, environment=environment)
    except AuditError as exc:
        raise click.ClickException(str(exc))

    if not entries:
        click.echo("No audit entries found.")
        return

    if tail is not None:
        entries = entries[-tail:]

    if output_format == "json":
        import dataclasses
        click.echo(json.dumps([dataclasses.asdict(e) for e in entries], indent=2))
    else:
        click.echo(format_log(entries))
