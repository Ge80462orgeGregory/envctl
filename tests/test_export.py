"""Unit tests for envctl.export."""

import json
import pytest

from envctl.export import export_env, ExportError, SUPPORTED_FORMATS


SAMPLE = {"DB_HOST": "localhost", "DB_PORT": "5432", 'SECRET': 'p@ss"word'}


class TestExportDotenv:
    def test_basic_output(self):
        result = export_env({"FOO": "bar"}, fmt="dotenv")
        assert 'FOO="bar"' in result

    def test_multiple_keys(self):
        result = export_env(SAMPLE, fmt="dotenv")
        assert 'DB_HOST="localhost"' in result
        assert 'DB_PORT="5432"' in result

    def test_escapes_double_quotes(self):
        result = export_env({"KEY": 'val"ue'}, fmt="dotenv")
        assert '\\"' in result

    def test_prefix_applied(self):
        result = export_env({"HOST": "db"}, fmt="dotenv", prefix="PROD")
        assert 'PROD_HOST="db"' in result
        assert "HOST=" not in result


class TestExportShell:
    def test_export_keyword(self):
        result = export_env({"FOO": "bar"}, fmt="shell")
        assert result.startswith("export ")

    def test_multiple_lines(self):
        result = export_env({"A": "1", "B": "2"}, fmt="shell")
        lines = result.splitlines()
        assert len(lines) == 2
        assert all(line.startswith("export ") for line in lines)

    def test_prefix_applied(self):
        result = export_env({"PORT": "8080"}, fmt="shell", prefix="STG")
        assert "STG_PORT" in result


class TestExportJson:
    def test_valid_json(self):
        result = export_env({"X": "1"}, fmt="json")
        parsed = json.loads(result)
        assert parsed == {"X": "1"}

    def test_prefix_in_keys(self):
        result = export_env({"KEY": "val"}, fmt="json", prefix="APP")
        parsed = json.loads(result)
        assert "APP_KEY" in parsed
        assert "KEY" not in parsed

    def test_empty_dict(self):
        result = export_env({}, fmt="json")
        assert json.loads(result) == {}


class TestExportErrors:
    def test_unsupported_format_raises(self):
        with pytest.raises(ExportError, match="Unsupported format"):
            export_env({"K": "v"}, fmt="yaml")

    def test_supported_formats_constant(self):
        assert "dotenv" in SUPPORTED_FORMATS
        assert "json" in SUPPORTED_FORMATS
        assert "shell" in SUPPORTED_FORMATS
