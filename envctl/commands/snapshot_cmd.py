"""CLI commands: snapshot take / snapshot restore."""

from __future__ import annotations

import json
import sys

import click

from envctl.snapshot import SnapshotError, Snapshot, take_snapshot, restore_snapshot


@click.group("snapshot")
def snapshot_cmd():
    """Take and restore environment snapshots."""


@snapshot_cmd.command("take")
@click.argument("project")
@click.argument("label")
@click.option("--output", "-o", type=click.Path(), default=None, help="Write snapshot JSON to file.")
def take_cmd(project: str, label: str, output: str | None):
    """Capture all environments for PROJECT under LABEL."""
    try:
        snap = take_snapshot(project, label)
    except SnapshotError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    payload = {
        "project": snap.project,
        "label": snap.label,
        "created_at": snap.created_at,
        "envs": snap.envs,
    }
    serialised = json.dumps(payload, indent=2)

    if output:
        with open(output, "w") as fh:
            fh.write(serialised)
        click.echo(f"Snapshot '{label}' for project '{project}' saved to {output}.")
    else:
        click.echo(serialised)


@snapshot_cmd.command("restore")
@click.argument("snapshot_file", type=click.Path(exists=True))
def restore_cmd(snapshot_file: str):
    """Restore environments from SNAPSHOT_FILE."""
    try:
        with open(snapshot_file) as fh:
            data = json.load(fh)
        snap = Snapshot(
            project=data["project"],
            label=data["label"],
            created_at=data["created_at"],
            envs=data["envs"],
        )
        result = restore_snapshot(snap)
    except (KeyError, ValueError) as exc:
        click.echo(f"Error: invalid snapshot file — {exc}", err=True)
        sys.exit(1)
    except SnapshotError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    click.echo(
        f"Restored snapshot '{result.label}' for project '{result.project}': "
        f"{len(result.restored_envs)} env(s), {result.total_keys} key(s)."
    )
