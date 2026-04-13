"""Tests for envctl.import_ and the import CLI command."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from envctl.commands.import_cmd import import_cmd
from envctl.import_ import ImportError, _parse_dotenv, _parse_json, import_env


# ---------------------------------------------------------------------------
# Unit tests – parsers
# ---------------------------------------------------------------------------

def test_parse_dotenv_basic():
    text = "FOO=bar\nBAZ=qux\n"
    assert _parse_dotenv(text) == {"FOO": "bar", "BAZ": "qux"}


def test_parse_dotenv_ignores_comments_and_blanks():
    text = "# comment\n\nFOO=bar\n"
    assert _parse_dotenv(text) == {"FOO": "bar"}


def test_parse_dotenv_strips_quotes():
    text = 'KEY="hello world"\n'
    assert _parse_dotenv(text) == {"KEY": "hello world"}


def test_parse_json_basic():
    text = json.dumps({"A": "1", "B": "2"})
    assert _parse_json(text) == {"A": "1", "B": "2"}


def test_parse_json_coerces_values():
    text = json.dumps({"NUM": 42})
    assert _parse_json(text) == {"NUM": "42"}


def test_parse_json_invalid_raises():
    with pytest.raises(ImportError, match="Invalid JSON"):
        _parse_json("not json")


def test_parse_json_non_object_raises():
    with pytest.raises(ImportError, match="object"):
        _parse_json(json.dumps(["a", "b"]))


# ---------------------------------------------------------------------------
# Unit tests – import_env
# ---------------------------------------------------------------------------

_EXISTING = {"KEEP": "old", "CONFLICT": "old_val"}
_INCOMING_TEXT = "CONFLICT=new_val\nNEW_KEY=hello\n"


@pytest.fixture()
def dotenv_file(tmp_path: Path) -> Path:
    p = tmp_path / "vars.env"
    p.write_text(_INCOMING_TEXT)
    return p


def _make_store(existing: dict):
    read = MagicMock(return_value=dict(existing))
    write = MagicMock()
    return read, write


def test_import_adds_new_keys_no_overwrite(dotenv_file: Path):
    read, write = _make_store(_EXISTING)
    with patch("envctl.import_.read_env", read), patch("envctl.import_.write_env", write):
        written = import_env("proj", "dev", dotenv_file, overwrite=False)
    assert "NEW_KEY" in written
    assert "CONFLICT" not in written  # skipped – no overwrite


def test_import_overwrites_when_flag_set(dotenv_file: Path):
    read, write = _make_store(_EXISTING)
    with patch("envctl.import_.read_env", read), patch("envctl.import_.write_env", write):
        written = import_env("proj", "dev", dotenv_file, overwrite=True)
    assert "CONFLICT" in written
    assert written["CONFLICT"] == "new_val"


def test_import_prefix_applied(dotenv_file: Path):
    read, write = _make_store({})
    with patch("envctl.import_.read_env", read), patch("envctl.import_.write_env", write):
        written = import_env("proj", "dev", dotenv_file, prefix="APP_")
    assert all(k.startswith("APP_") for k in written)


def test_import_missing_file_raises(tmp_path: Path):
    with pytest.raises(ImportError, match="not found"):
        import_env("proj", "dev", tmp_path / "missing.env")


def test_import_unsupported_format_raises(dotenv_file: Path):
    with pytest.raises(ImportError, match="Unsupported format"):
        import_env("proj", "dev", dotenv_file, fmt="yaml")


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def runner():
    return CliRunner()


def test_import_cmd_success(runner: CliRunner, dotenv_file: Path):
    read, write = _make_store({})
    with patch("envctl.import_.read_env", read), patch("envctl.import_.write_env", write):
        result = runner.invoke(import_cmd, ["proj", "dev", str(dotenv_file)])
    assert result.exit_code == 0
    assert "Imported" in result.output


def test_import_cmd_nothing_to_import(runner: CliRunner, dotenv_file: Path):
    # All keys already exist with identical values
    existing = {"CONFLICT": "new_val", "NEW_KEY": "hello"}
    read, write = _make_store(existing)
    with patch("envctl.import_.read_env", read), patch("envctl.import_.write_env", write):
        result = runner.invoke(import_cmd, ["proj", "dev", str(dotenv_file)])
    assert result.exit_code == 0
    assert "Nothing" in result.output


def test_import_cmd_missing_file_error(runner: CliRunner, tmp_path: Path):
    result = runner.invoke(
        import_cmd, ["proj", "dev", str(tmp_path / "ghost.env")]
    )
    assert result.exit_code != 0
    assert "Error" in result.output
