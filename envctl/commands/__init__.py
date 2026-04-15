"""CLI entry-point — registers all sub-commands."""
from __future__ import annotations

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
from envctl.commands.protect_cmd import protect_cmd
from envctl.commands.placeholder_cmd import placeholder_cmd
from envctl.commands.flatten_cmd import flatten_cmd
from envctl.commands.resolve_cmd import resolve_cmd
from envctl.commands.reorder_cmd import reorder_cmd
from envctl.commands.encrypt_cmd import encrypt_cmd
from envctl.commands.watch_cmd import watch_cmd
from envctl.commands.history_cmd import history_cmd
from envctl.commands.summarize_cmd import summarize_cmd
from envctl.commands.fmt_cmd import fmt_cmd
from envctl.commands.grep_cmd import grep_cmd
from envctl.commands.cast_cmd import cast_cmd


@click.group()
@click.version_option()
def cli() -> None:  # pragma: no cover
    """envctl — manage and sync environment variable sets."""


cli.add_command(diff_cmd, "diff")
cli.add_command(sync_cmd, "sync")
cli.add_command(copy_cmd, "copy")
cli.add_command(rename_cmd, "rename")
cli.add_command(export_cmd, "export")
cli.add_command(delete_cmd, "delete")
cli.add_command(import_cmd, "import")
cli.add_command(list_cmd, "list")
cli.add_command(promote_cmd, "promote")
cli.add_command(audit_cmd, "audit")
cli.add_command(validate_cmd, "validate")
cli.add_command(merge_cmd, "merge")
cli.add_command(snapshot_cmd, "snapshot")
cli.add_command(search_cmd, "search")
cli.add_command(protect_cmd, "protect")
cli.add_command(placeholder_cmd, "placeholder")
cli.add_command(flatten_cmd, "flatten")
cli.add_command(resolve_cmd, "resolve")
cli.add_command(reorder_cmd, "reorder")
cli.add_command(encrypt_cmd, "encrypt")
cli.add_command(watch_cmd, "watch")
cli.add_command(history_cmd, "history")
cli.add_command(summarize_cmd, "summarize")
cli.add_command(fmt_cmd, "fmt")
cli.add_command(grep_cmd, "grep")
cli.add_command(cast_cmd, "cast")
