"""CLI command for viewing environment variable change history."""

import json
import click
from envctl.config import load_config, get_envs_dir
from envctl.history import read_history, HistoryError


@click.command("history")
@click.argument("project")
@click.argument("environment")
@click.option("-n", "--limit", default=None, type=int, help="Max entries to show.")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    show_default=True,
    help="Output format.",
)
def history_cmd(project: str, environment: str, limit, output_format: str) -> None:
    """Show change history for PROJECT / ENVIRONMENT."""
    try:
        cfg = load_config()
        envs_dir = get_envs_dir(cfg)
        entries = read_history(envs_dir, project, environment, limit=limit)
    except HistoryError as exc:
        raise click.ClickException(str(exc)) from exc

    if not entries:
        click.echo("No history found.")
        return

    if output_format == "json":
        click.echo(json.dumps([e.to_dict() for e in entries], indent=2))
        return

    for entry in entries:
        actor_part = f" [{entry.actor}]" if entry.actor else ""
        click.echo(
            f"{entry.timestamp}  {entry.action.upper()}{actor_part}  "
            f"{entry.project}/{entry.environment}"
        )
        for key, detail in entry.changes.items():
            click.echo(f"  {key}: {detail}")
