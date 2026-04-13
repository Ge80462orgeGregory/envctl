"""envctl CLI entry point — registers all sub-commands."""
import click

from envctl.commands.diff_cmd import diff_cmd
from envctl.commands.sync_cmd import sync_cmd
from envctl.commands.copy_cmd import copy_cmd
from envctl.commands.rename_cmd import rename_cmd
from envctl.commands.export_cmd import export_cmd
from envctl.commands.delete_cmd import delete_cmd
from envctl.commands.import_cmd import import_cmd
from envctl.commands.list_cmd import list_cmd
from envctl.commands.promote_cmd import promote_cmd
from envctl.commands.audit_cmd import audit_cmd
from envctl.commands.validate_cmd import validate_cmd
from envctl.commands.merge_cmd import merge_cmd
from envctl.commands.snapshot_cmd import snapshot_cmd
from envctl.commands.search_cmd import search_cmd
from envctl.commands.watch_cmd import watch_cmd


@click.group()
@click.version_option()
@click.pass_context
def cli(ctx: click.Context) -> None:
    """envctl — manage and sync environment variable sets."""
    ctx.ensure_object(dict)


cli.add_command(diff_cmd)
cli.add_command(sync_cmd)
cli.add_command(copy_cmd)
cli.add_command(rename_cmd)
cli.add_command(export_cmd)
cli.add_command(delete_cmd)
cli.add_command(import_cmd)
cli.add_command(list_cmd)
cli.add_command(promote_cmd)
cli.add_command(audit_cmd)
cli.add_command(validate_cmd)
cli.add_command(merge_cmd)
cli.add_command(snapshot_cmd)
cli.add_command(search_cmd)
cli.add_command(watch_cmd)
