"""CLI command for searching keys/values across environments."""

import json
import sys

import click

from envctl.search import SearchError, format_search, search_envs
from envctl.config import load_config, get_envs_dir
from envctl.env_store import list_projects, list_environments, read_env


@click.command("search")
@click.argument("query")
@click.option("--project", "-p", default=None, help="Limit search to a specific project.")
@click.option("--keys-only", is_flag=True, default=False, help="Search only in key names.")
@click.option("--values-only", is_flag=True, default=False, help="Search only in values.")
@click.option("--case-sensitive", is_flag=True, default=False, help="Case-sensitive matching.")
@click.option("--hide-values", is_flag=True, default=False, help="Do not print matched values.")
@click.option("--format", "output_format", type=click.Choice(["text", "json"]), default="text")
def search_cmd(
    query,
    project,
    keys_only,
    values_only,
    case_sensitive,
    hide_values,
    output_format,
):
    """Search for QUERY across environment keys and values."""
    search_keys = not values_only
    search_values = not keys_only

    try:
        result = search_envs(
            query,
            project=project,
            search_keys=search_keys,
            search_values=search_values,
            case_sensitive=case_sensitive,
            read_fn=read_env,
            list_projects_fn=list_projects,
            list_environments_fn=list_environments,
        )
    except SearchError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    if output_format == "json":
        payload = [
            {
                "project": m.project,
                "environment": m.environment,
                "key": m.key,
                "value": m.value if not hide_values else None,
            }
            for m in result.matches
        ]
        click.echo(json.dumps(payload, indent=2))
    else:
        click.echo(format_search(result, show_values=not hide_values))

    if result.total == 0:
        sys.exit(1)
