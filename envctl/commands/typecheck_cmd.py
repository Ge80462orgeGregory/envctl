import json
import click
from envctl.typecheck import typecheck_env, TypeCheckError
from envctl.env_store import read_env
from envctl.config import load_config, get_envs_dir


def _read(project: str, environment: str):
    config = load_config()
    envs_dir = get_envs_dir(config)
    return read_env(envs_dir, project, environment)


@click.command("typecheck")
@click.argument("project")
@click.argument("environment")
@click.option("--schema", "-s", multiple=True, metavar="KEY:TYPE",
              help="Expected type for a key, e.g. PORT:int")
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
def typecheck_cmd(project, environment, schema, fmt):
    """Check that env variable values match expected types."""
    parsed_schema = {}
    for entry in schema:
        if ":" not in entry:
            raise click.UsageError(f"Schema entry must be KEY:TYPE, got '{entry}'")
        key, typ = entry.split(":", 1)
        parsed_schema[key.strip()] = typ.strip()

    if not parsed_schema:
        raise click.UsageError("Provide at least one --schema KEY:TYPE entry.")

    try:
        result = typecheck_env(project, environment, parsed_schema, _read)
    except TypeCheckError as e:
        raise click.ClickException(str(e))

    if fmt == "json":
        click.echo(json.dumps(result.to_dict(), indent=2))
        return

    click.echo(f"Project:     {result.project}")
    click.echo(f"Environment: {result.environment}")
    click.echo(f"Checked:     {result.checked} key(s)")

    if result.passed:
        click.echo("Result:      ✓ All type checks passed.")
    else:
        click.echo(f"Result:      ✗ {len(result.issues)} issue(s) found.")
        for issue in result.issues:
            click.echo(
                f"  [{issue.key}] expected={issue.expected_type} "
                f"inferred={issue.actual_inferred} value={issue.value!r}"
            )
        raise SystemExit(1)
