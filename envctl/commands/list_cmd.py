"""CLI command: list projects and environments."""

import click

from envctl.config import load_config, get_envs_dir
from envctl.list_ import list_all, list_project_envs, format_list, ListError


@click.command("list")
@click.argument("project", required=False, default=None)
@click.option(
    "--json", "as_json", is_flag=True, default=False,
    help="Output results as JSON."
)
def list_cmd(project: str, as_json: bool) -> None:
    """List all projects and their environments, or environments for a PROJECT."""
    config = load_config()
    envs_dir = get_envs_dir(config)

    try:
        if project:
            results = [list_project_envs(envs_dir, project)]
        else:
            results = list_all(envs_dir)
    except ListError as exc:
        raise click.ClickException(str(exc)) from exc

    if as_json:
        import json
        data = [
            {"project": r.project, "environments": r.entries}
            for r in results
        ]
        click.echo(json.dumps(data, indent=2))
    else:
        click.echo(format_list(results))
