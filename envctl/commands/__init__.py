"""envctl CLI entry-point — registers all sub-commands."""
from __future__ import annotations

import click

from envctl.commands.diff_cmd import diff_cmd
from envctl.commands.sync_cmd import sync_cmd
from envctl.commands.copy_cmd import copy_cmd
from envctl.commands.rename_cmd import rename_cmd
from envctl.commands.export_cmd import export_cmd
from envctl.commands.import_cmd import import_cmd
from envctl.commands.list_cmd import list_cmd
from envctl.commands.delete_cmd import delete_cmd
from envctl.commands.promote_cmd import promote_cmd
from envctl.commands.audit_cmd import audit_cmd
from envctl.commands.validate_cmd import validate_cmd
from envctl.commands.merge_cmd import merge_cmd
from envctl.commands.snapshot_cmd import snapshot_cmd
from envctl.commands.search_cmd import search_cmd
from envctl.commands.protect_cmd import protect_cmd
from envctl.commands.flatten_cmd import flatten_cmd
from envctl.commands.resolve_cmd import resolve_cmd
from envctl.commands.reorder_cmd import reorder_cmd
from envctl.commands.encrypt_cmd import encrypt_cmd
from envctl.commands.summarize_cmd import summarize_cmd
from envctl.commands.fmt_cmd import fmt_cmd
from envctl.commands.grep_cmd import grep_cmd
from envctl.commands.cast_cmd import cast_cmd
from envctl.commands.filter_cmd import filter_cmd
from envctl.commands.rename_key_cmd import rename_key_cmd
from envctl.commands.squash_cmd import squash_cmd
from envctl.commands.count_cmd import count_cmd
from envctl.commands.typecheck_cmd import typecheck_cmd
from envctl.commands.prefix_cmd import prefix_cmd
from envctl.commands.required_cmd import required_cmd
from envctl.commands.defaults_cmd import defaults_cmd
from envctl.commands.intersect_cmd import intersect_cmd
from envctl.commands.swap_cmd import swap_cmd
from envctl.commands.upper_cmd import upper_cmd
from envctl.commands.lowercase_cmd import lowercase_cmd
from envctl.commands.unique_cmd import unique_cmd
from envctl.commands.group_cmd import group_cmd
from envctl.commands.suffix_cmd import suffix_cmd
from envctl.commands.pivot_cmd import pivot_cmd
from envctl.commands.align_cmd import align_cmd
from envctl.commands.inspect_cmd import inspect_cmd
from envctl.commands.prune_cmd import prune_cmd
from envctl.commands.annotate_cmd import annotate_cmd
from envctl.commands.migrate_cmd import migrate_cmd
from envctl.commands.extract_cmd import extract_cmd
from envctl.commands.watch_cmd import watch_cmd
from envctl.commands.history_cmd import history_cmd
from envctl.commands.placeholder_cmd import placeholder_cmd
from envctl.commands.substitute_cmd import substitute_cmd


@click.group()
@click.version_option()
def cli() -> None:  # pragma: no cover
    """envctl — manage and sync environment variable sets."""


# core env management
cli.add_command(list_cmd, name="list")
cli.add_command(diff_cmd, name="diff")
cli.add_command(sync_cmd, name="sync")
cli.add_command(copy_cmd, name="copy")
cli.add_command(rename_cmd, name="rename")
cli.add_command(delete_cmd, name="delete")
cli.add_command(export_cmd, name="export")
cli.add_command(import_cmd, name="import")
cli.add_command(promote_cmd, name="promote")
cli.add_command(merge_cmd, name="merge")
cli.add_command(snapshot_cmd, name="snapshot")
cli.add_command(validate_cmd, name="validate")
cli.add_command(audit_cmd, name="audit")
cli.add_command(search_cmd, name="search")
cli.add_command(protect_cmd, name="protect")
cli.add_command(flatten_cmd, name="flatten")
cli.add_command(resolve_cmd, name="resolve")
cli.add_command(reorder_cmd, name="reorder")
cli.add_command(encrypt_cmd, name="encrypt")
cli.add_command(summarize_cmd, name="summarize")
cli.add_command(fmt_cmd, name="fmt")
cli.add_command(grep_cmd, name="grep")
cli.add_command(cast_cmd, name="cast")
cli.add_command(filter_cmd, name="filter")
cli.add_command(rename_key_cmd, name="rename-key")
cli.add_command(squash_cmd, name="squash")
cli.add_command(count_cmd, name="count")
cli.add_command(typecheck_cmd, name="typecheck")
cli.add_command(prefix_cmd, name="prefix")
cli.add_command(required_cmd, name="required")
cli.add_command(defaults_cmd, name="defaults")
cli.add_command(intersect_cmd, name="intersect")
cli.add_command(swap_cmd, name="swap")
cli.add_command(upper_cmd, name="upper")
cli.add_command(lowercase_cmd, name="lowercase")
cli.add_command(unique_cmd, name="unique")
cli.add_command(group_cmd, name="group")
cli.add_command(suffix_cmd, name="suffix")
cli.add_command(pivot_cmd, name="pivot")
cli.add_command(align_cmd, name="align")
cli.add_command(inspect_cmd, name="inspect")
cli.add_command(prune_cmd, name="prune")
cli.add_command(annotate_cmd, name="annotate")
cli.add_command(migrate_cmd, name="migrate")
cli.add_command(extract_cmd, name="extract")
cli.add_command(watch_cmd, name="watch")
cli.add_command(history_cmd, name="history")
cli.add_command(placeholder_cmd, name="placeholder")
cli.add_command(substitute_cmd, name="substitute")
