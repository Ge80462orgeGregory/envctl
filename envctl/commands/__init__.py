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
from envctl.commands.summarize_cmd import summarize_cmd
from envctl.commands.fmt_cmd import fmt_cmd
from envctl.commands.grep_cmd import grep_cmd
from envctl.commands.cast_cmd import cast_cmd
from envctl.commands.filter_cmd import filter_cmd
from envctl.commands.rename_key_cmd import rename_key_cmd
from envctl.commands.squash_cmd import squash_cmd
from envctl.commands.annotate_cmd import annotate_cmd
from envctl.commands.migrate_cmd import migrate_cmd
from envctl.commands.extract_cmd import extract_cmd
from envctl.commands.prune_cmd import prune_cmd
from envctl.commands.inspect_cmd import inspect_cmd
from envctl.commands.watch_cmd import watch_cmd
from envctl.commands.history_cmd import history_cmd
from envctl.commands.count_cmd import count_cmd


@click.group()
def cli() -> None:
    """envctl — manage and sync environment variable sets."""


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
cli.add_command(protect_cmd)
cli.add_command(placeholder_cmd)
cli.add_command(flatten_cmd)
cli.add_command(resolve_cmd)
cli.add_command(reorder_cmd)
cli.add_command(encrypt_cmd)
cli.add_command(summarize_cmd)
cli.add_command(fmt_cmd)
cli.add_command(grep_cmd)
cli.add_command(cast_cmd)
cli.add_command(filter_cmd)
cli.add_command(rename_key_cmd)
cli.add_command(squash_cmd)
cli.add_command(annotate_cmd)
cli.add_command(migrate_cmd)
cli.add_command(extract_cmd)
cli.add_command(prune_cmd)
cli.add_command(inspect_cmd)
cli.add_command(watch_cmd)
cli.add_command(history_cmd)
cli.add_command(count_cmd)
