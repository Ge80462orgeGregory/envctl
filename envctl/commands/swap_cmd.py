"""CLI command for swapping two key values in an environment."""
import json
import click
from envctl.swap import swap_keys, SwapError
from envctl.env_store import read_env, write_env
from envctl.config import load_config, get_envs_dir


@click.command("swap")
@click.argument("project")
@click.argument("environment")
@click.argument("key_a")
@click.argument("key_b")
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
def swap_cmd(project: str, environment: str, key_a: str, key_b: str, fmt: str) -> None:
    """Swap the values of KEY_A and KEY_B in PROJECT/ENVIRONMENT."""
    config = load_config()
    envs_dir = get_envs_dir(config)

    def _read(p, e):
        return read_env(envs_dir, p, e)

    def _write(p, e, data):
        return write_env(envs_dir, p, e, data)

    try:
        result = swap_keys(project, environment, key_a, key_b, _read, _write)
    except SwapError as exc:
        raise click.ClickException(str(exc))

    if fmt == "json":
        click.echo(json.dumps(result.to_dict(), indent=2))
    else:
        click.echo(
            f"Swapped '{result.key_a}' and '{result.key_b}' "
            f"in {result.project}/{result.environment}."
        )
        click.echo(f"  {result.key_a} = {result.value_b}  (was: {result.value_a})")
        click.echo(f"  {result.key_b} = {result.value_a}  (was: {result.value_b})")
