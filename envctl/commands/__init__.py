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

# Mapping of command name -> command object for bulk registration.
_COMMANDS: list[tuple[click.BaseCommand, str]] = [
    (diff_cmd, "diff"),
    (sync_cmd, "sync"),
    (copy_cmd, "copy"),
    (rename_cmd, "rename"),
    (export_cmd, "export"),
    (delete_cmd, "delete"),
    (import_cmd, "import"),
    (list_cmd, "list"),
    (promote_cmd, "promote"),
    (audit_cmd, "audit"),
    (validate_cmd, "validate"),
    (merge_cmd, "merge"),
    (snapshot_cmd, "snapshot"),
    (search_cmd, "search"),
    (protect_cmd, "protect"),
    (placeholder_cmd, "placeholder"),
    (flatten_cmd, "flatten"),
    (resolve_cmd, "resolve"),
    (reorder_cmd, "reorder"),
    (encrypt_cmd, "encrypt"),
    (watch_cmd, "watch"),
    (history_cmd, "history"),
    (summarize_cmd, "summarize"),
    (fmt_cmd, "fmt"),
    (grep_cmd, "grep"),
    (cast_cmd, "cast"),
]


@click.group()
@click.version_option()
def cli() -> None:  # pragma: no cover
    """envctl — manage and sync environment variable sets."""


for _cmd, _name in _COMMANDS:
    cli.add_command(_cmd, _name)
