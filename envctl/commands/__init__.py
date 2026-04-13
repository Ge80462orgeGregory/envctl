"""Register all envctl CLI commands."""
import click

from envctl.commands.diff_cmd import diff_cmd
from envctl.commands.sync_cmd import sync_cmd
from envctl.commands.copy_cmd import copy_cmd
from envctl.commands.rename_cmd import rename_cmd
from envctl.commands.export_cmd import export_cmd
from envctl.commands.import_cmd import import_cmd
from envctl.commands.delete_cmd import delete_cmd
from envctl.commands.list_cmd import list_cmd
from envctl.commands.promote_cmd import promote_cmd
from envctl.commands.audit_cmd import audit_cmd
from envctl.commands.validate_cmd import validate_cmd


@click.group()
def cli() -> None:
    """envctl — manage and sync environment variable sets."""


for _cmd in (
    diff_cmd,
    sync_cmd,
    copy_cmd,
    rename_cmd,
    export_cmd,
    import_cmd,
    delete_cmd,
    list_cmd,
    promote_cmd,
    audit_cmd,
    validate_cmd,
):
    cli.add_command(_cmd)
