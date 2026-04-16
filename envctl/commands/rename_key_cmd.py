import click
import json
from envctl.rename_key import rename_key, RenameKeyError
from envctl.config import load_config, get_envs_dir
from envctl.env_store import read_env, write_env


@click.command("rename-key")
@click.argument("project")
@click.argument("environment")
@click.argument("old_key")
@click.argument("new_key")
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]), help="Output format")
def rename_key_cmd(project, environment, old_key, new_key, fmt):
    """Rename a key within an environment."""
    cfg = load_config()
    envs_dir = get_envs_dir(cfg)

    def _read(p, e):
        return read_env(p, e, envs_dir=envs_dir)

    def _write(p, e, data):
        return write_env(p, e, data, envs_dir=envs_dir)

    try:
        result = rename_key(project, environment, old_key, new_key, read=_read, write=_write)
    except RenameKeyError as exc:
        raise click.ClickException(str(exc))

    if fmt == "json":
        click.echo(json.dumps(result.to_dict(), indent=2))
    else:
        click.echo(
            f"Renamed '{result.old_key}' -> '{result.new_key}' "
            f"in {result.project}/{result.environment}"
        )
