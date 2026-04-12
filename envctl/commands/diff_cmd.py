"""CLI command: envctl diff <project> <env_a> <env_b>"""

import click

from envctl.config import load_config, get_envs_dir
from envctl.env_store import read_env
from envctl.diff import diff_envs, format_diff


@click.command(name="diff")
@click.argument("project")
@click.argument("env_a")
@click.argument("env_b")
@click.option(
    "--show-values",
    is_flag=True,
    default=False,
    help="Show actual values instead of masking them.",
)
def diff_cmd(project: str, env_a: str, env_b: str, show_values: bool) -> None:
    """Diff environment variables between ENV_A and ENV_B for PROJECT.

    Example:
        envctl diff myapp local staging
    """
    cfg = load_config()
    envs_dir = get_envs_dir(cfg)

    vars_a = read_env(envs_dir, project, env_a)
    vars_b = read_env(envs_dir, project, env_b)

    if not vars_a and not vars_b:
        click.echo(
            f"No variables found for project '{project}' in either "
            f"'{env_a}' or '{env_b}'."
        )
        raise SystemExit(1)

    result = diff_envs(vars_a, vars_b)
    mask = not show_values

    click.echo(f"\nDiff for '{project}': {env_a} -> {env_b}")
    click.echo("-" * 40)
    click.echo(format_diff(result, mask_values=mask))
