"""Unit tests for envctl.fmt."""

from __future__ import annotations

import json
import pytest

from envctl.fmt import format_env, FmtError


SAMPLE = {"DB_HOST": "localhost", "API_KEY": "secret", "PORT": "5432"}


# ---------------------------------------------------------------------------
# dotenv style
# ---------------------------------------------------------------------------

def test_dotenv_style_keys_sorted():
    result = format_env("myapp", "dev", SAMPLE, style="dotenv")
    keys = [line.split("=")[0] for line in result.lines]
    assert keys == sorted(keys)


def test_dotenv_style_quotes_values():
    result = format_env("myapp", "dev", {"KEY": "value"}, style="dotenv")
    assert result.lines == ['KEY="value"']


def test_dotenv_style_escapes_double_quotes():
    result = format_env("myapp", "dev", {"KEY": 'say "hi"'}, style="dotenv")
    assert result.lines == ['KEY="say \\"hi\\""']


# ---------------------------------------------------------------------------
# shell style
# ---------------------------------------------------------------------------

def test_shell_style_uses_export():
    result = format_env("myapp", "dev", {"FOO": "bar"}, style="shell")
    assert result.lines == ['export FOO="bar"']


def test_shell_style_sorted():
    result = format_env("myapp", "dev", SAMPLE, style="shell")
    keys = [line.split(" ")[1].split("=")[0] for line in result.lines]
    assert keys == sorted(keys)


# ---------------------------------------------------------------------------
# json style
# ---------------------------------------------------------------------------

def test_json_style_valid_json():
    result = format_env("myapp", "dev", SAMPLE, style="json")
    parsed = json.loads(result.rendered)
    assert parsed == SAMPLE


def test_json_style_keys_sorted():
    result = format_env("myapp", "dev", SAMPLE, style="json")
    parsed = json.loads(result.rendered)
    assert list(parsed.keys()) == sorted(parsed.keys())


# ---------------------------------------------------------------------------
# table style
# ---------------------------------------------------------------------------

def test_table_style_has_header():
    result = format_env("myapp", "dev", SAMPLE, style="table")
    assert result.lines[0].startswith("KEY")


def test_table_style_empty_env():
    result = format_env("myapp", "dev", {}, style="table")
    assert result.rendered == "(no variables)"


# ---------------------------------------------------------------------------
# FmtResult helpers
# ---------------------------------------------------------------------------

def test_result_metadata():
    result = format_env("proj", "staging", {"A": "1"}, style="dotenv")
    assert result.project == "proj"
    assert result.environment == "staging"
    assert result.style == "dotenv"


def test_result_to_dict_contains_output():
    result = format_env("proj", "staging", {"A": "1"}, style="dotenv")
    d = result.to_dict()
    assert "output" in d
    assert d["style"] == "dotenv"


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

def test_unknown_style_raises():
    with pytest.raises(FmtError, match="Unknown format style"):
        format_env("proj", "dev", {"A": "1"}, style="yaml")  # type: ignore[arg-type]
