"""Tests for envctl.archive module."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from envctl.archive import (
    ArchiveError,
    ArchiveResult,
    ExtractResult,
    archive_project,
    extract_archive,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_STORE: dict[tuple[str, str], dict[str, str]] = {}


def _make_list(mapping: dict[str, list[str]]):
    def _list(project: str) -> list[str]:
        return mapping.get(project, [])
    return _list


def _make_read(data: dict[tuple[str, str], dict[str, str]]):
    def _read(project: str, env: str) -> dict[str, str]:
        return dict(data.get((project, env), {}))
    return _read


_written: dict[tuple[str, str], dict[str, str]] = {}


def _write(project: str, env: str, variables: dict[str, str]) -> None:
    _written[(project, env)] = dict(variables)


# ---------------------------------------------------------------------------
# archive_project
# ---------------------------------------------------------------------------

def test_archive_creates_zip(tmp_path: Path) -> None:
    data = {("myapp", "local"): {"A": "1"}, ("myapp", "prod"): {"B": "2"}}
    result = archive_project(
        "myapp",
        str(tmp_path),
        _make_list({"myapp": ["local", "prod"]}),
        _make_read(data),
    )
    assert isinstance(result, ArchiveResult)
    assert Path(result.archive_path).exists()
    assert result.environments == ["local", "prod"]
    assert result.total_keys == 2


def test_archive_zip_contains_expected_entries(tmp_path: Path) -> None:
    data = {("app", "staging"): {"X": "hello"}}
    result = archive_project(
        "app",
        str(tmp_path),
        _make_list({"app": ["staging"]}),
        _make_read(data),
    )
    with zipfile.ZipFile(result.archive_path) as zf:
        names = zf.namelist()
    assert "meta.json" in names
    assert "staging.json" in names


def test_archive_raises_when_no_environments(tmp_path: Path) -> None:
    with pytest.raises(ArchiveError, match="No environments"):
        archive_project(
            "empty",
            str(tmp_path),
            _make_list({}),
            _make_read({}),
        )


# ---------------------------------------------------------------------------
# extract_archive
# ---------------------------------------------------------------------------

def _make_archive(tmp_path: Path, project: str, envs: dict[str, dict[str, str]]) -> str:
    archive_path = str(tmp_path / f"{project}.envctl.zip")
    with zipfile.ZipFile(archive_path, "w") as zf:
        meta = {"project": project, "created_at": "20240101T000000Z", "environments": list(envs)}
        zf.writestr("meta.json", json.dumps(meta))
        for env, variables in envs.items():
            zf.writestr(f"{env}.json", json.dumps(variables))
    return archive_path


def test_extract_restores_environments(tmp_path: Path) -> None:
    _written.clear()
    archive = _make_archive(tmp_path, "proj", {"dev": {"K": "v"}, "prod": {"M": "n"}})
    result = extract_archive(archive, _write)
    assert isinstance(result, ExtractResult)
    assert set(result.environments_restored) == {"dev", "prod"}
    assert result.total_keys == 2
    assert _written[("proj", "dev")] == {"K": "v"}


def test_extract_overwrite_replaces_existing(tmp_path: Path) -> None:
    _written.clear()
    existing = {("proj", "dev"): {"K": "old", "Z": "keep"}}
    archive = _make_archive(tmp_path, "proj", {"dev": {"K": "new"}})
    extract_archive(archive, _write, overwrite=True, read_env=_make_read(existing))
    assert _written[("proj", "dev")] == {"K": "new"}


def test_extract_no_overwrite_preserves_existing(tmp_path: Path) -> None:
    _written.clear()
    existing = {("proj", "dev"): {"K": "old", "Z": "keep"}}
    archive = _make_archive(tmp_path, "proj", {"dev": {"K": "new"}})
    extract_archive(archive, _write, overwrite=False, read_env=_make_read(existing))
    assert _written[("proj", "dev")]["K"] == "old"
    assert _written[("proj", "dev")]["Z"] == "keep"


def test_extract_raises_for_missing_file(tmp_path: Path) -> None:
    with pytest.raises(ArchiveError, match="not found"):
        extract_archive(str(tmp_path / "nonexistent.zip"), _write)


def test_extract_raises_for_invalid_archive(tmp_path: Path) -> None:
    bad = tmp_path / "bad.zip"
    with zipfile.ZipFile(str(bad), "w") as zf:
        zf.writestr("junk.txt", "hello")
    with pytest.raises(ArchiveError, match="Invalid archive"):
        extract_archive(str(bad), _write)
