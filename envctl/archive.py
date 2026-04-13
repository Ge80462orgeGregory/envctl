"""Archive and restore environment variable sets as compressed bundles."""

from __future__ import annotations

import json
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable


class ArchiveError(Exception):
    """Raised when an archive operation fails."""


@dataclass
class ArchiveResult:
    project: str
    archive_path: str
    environments: list[str] = field(default_factory=list)
    total_keys: int = 0


@dataclass
class ExtractResult:
    project: str
    archive_path: str
    environments_restored: list[str] = field(default_factory=list)
    total_keys: int = 0


def archive_project(
    project: str,
    dest_dir: str,
    list_environments: Callable[[str], list[str]],
    read_env: Callable[[str, str], dict[str, str]],
) -> ArchiveResult:
    """Bundle all environments for *project* into a zip archive."""
    envs = list_environments(project)
    if not envs:
        raise ArchiveError(f"No environments found for project '{project}'")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    archive_name = f"{project}_{timestamp}.envctl.zip"
    archive_path = str(Path(dest_dir) / archive_name)

    total_keys = 0
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        meta = {"project": project, "created_at": timestamp, "environments": envs}
        zf.writestr("meta.json", json.dumps(meta, indent=2))
        for env in envs:
            variables = read_env(project, env)
            total_keys += len(variables)
            zf.writestr(f"{env}.json", json.dumps(variables, indent=2))

    return ArchiveResult(
        project=project,
        archive_path=archive_path,
        environments=envs,
        total_keys=total_keys,
    )


def extract_archive(
    archive_path: str,
    write_env: Callable[[str, str, dict[str, str]], None],
    overwrite: bool = False,
    read_env: Callable[[str, str], dict[str, str]] | None = None,
) -> ExtractResult:
    """Restore environments from a previously created archive."""
    path = Path(archive_path)
    if not path.exists():
        raise ArchiveError(f"Archive not found: {archive_path}")

    with zipfile.ZipFile(archive_path, "r") as zf:
        names = zf.namelist()
        if "meta.json" not in names:
            raise ArchiveError("Invalid archive: missing meta.json")

        meta = json.loads(zf.read("meta.json"))
        project = meta["project"]
        environments = meta.get("environments", [])

        total_keys = 0
        restored: list[str] = []
        for env in environments:
            entry = f"{env}.json"
            if entry not in names:
                continue
            incoming: dict[str, str] = json.loads(zf.read(entry))
            if not overwrite and read_env is not None:
                existing = read_env(project, env)
                merged = {**incoming, **existing}
            else:
                merged = incoming
            write_env(project, env, merged)
            total_keys += len(merged)
            restored.append(env)

    return ExtractResult(
        project=project,
        archive_path=archive_path,
        environments_restored=restored,
        total_keys=total_keys,
    )
