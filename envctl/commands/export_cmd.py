"""CLI command: export an environment to stdout or a file."""

import sys
import click

from envctl.config import load_config, get_envs_dir
from envctl.env_store import read_env
from envctl.export import export_env, ExportError, SUPPORTED_FORMATS


@click.command("export")
@click.argument("project")
@click.argument("environment")
@click.option(
    "--format",
    "fmt",
    default="dotenv",
    show_default=True,
    type=click.Choice(list(SUPPORTED_FORMATS), case_sensitive=False),
    help="Output format.",
)
@click.option(
    "--prefix",
    default=None,
    help="Optional prefix prepended to every variable name.",
)
@click.option(
    "--output",
    "-o",
    default=None,
    type=click.Path(dir_okay=False, writable=True),
    help="Write output to FILE instead of stdout.",
)
def export_cmd(project: str, environment: str, fmt: str, prefix: str, output: str) -> None:
    """Export PROJECT/ENVIRONMENT variables to a chosen format."""
    config = load_config()
    envs_dir = get_envs_dir(config)

    variables = read_env(envs_dir, project, environment)

    if not variables:
        click.echo(
            f"No variables found for '{project}/{environment}'.", err=True
        )
        sys.exit(1)

    try:
        result = export_env(variables, fmt=fmt, prefix=prefix)
    except ExportError as exc:
        click.echo(f"Export error: {exc}", err=True)
        sys.exit(1)

    if output:
        _write_to_file(output, result, len(variables))
    else:
        click.echo(result)


def _write_to_file(path: str, content: str, variable_count: int) -> None:
    """Write exported content to a file and print a confirmation message.

    Args:
        path: Destination file path.
        content: The formatted export string to write.
        variable_count: Number of variables exported, used in the confirmation.
    """
    try:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content + "\n")
    except OSError as exc:
        click.echo(f"Failed to write to '{path}': {exc}", err=True)
        sys.exit(1)
    click.echo(f"Exported {variable_count} variable(s) to '{path}'.")
