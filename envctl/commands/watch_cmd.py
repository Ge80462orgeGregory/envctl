"""CLI command for watching environment variable changes."""
import json
import sys
import time

import click

from envctl.watch import take_watch_snapshot, compare_watch_snapshot, WatchError
from envctl.config import load_config


@click.command("watch")
@click.argument("project")
@click.argument("environment")
@click.option("--interval", default=5, show_default=True, help="Poll interval in seconds.")
@click.option("--once", is_flag=True, default=False, help="Check once and exit.")
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text", show_default=True)
@click.pass_context
def watch_cmd(ctx: click.Context, project: str, environment: str, interval: int, once: bool, fmt: str) -> None:
    """Watch PROJECT/ENVIRONMENT for variable changes."""
    cfg = load_config()
    try:
        snapshot = take_watch_snapshot(project, environment)
    except WatchError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    click.echo(f"Watching {project}/{environment} (interval={interval}s) ...")

    while True:
        time.sleep(interval)
        result = compare_watch_snapshot(snapshot)
        if result.has_changes:
            if fmt == "json":
                click.echo(json.dumps({
                    "project": result.project,
                    "environment": result.environment,
                    "diff": result.diff_lines,
                }))
            else:
                click.echo(f"\n[{result.project}/{result.environment}] Changes detected:")
                for line in result.diff_lines:
                    click.echo(line)
            snapshot = take_watch_snapshot(project, environment)
        else:
            if fmt == "text":
                click.echo(".", nl=False)

        if once:
            break
