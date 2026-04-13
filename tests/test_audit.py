"""Tests for envctl.audit module."""

import os
import pytest

from envctl.audit import record, read_log, format_log, AuditError, _audit_file_path


@pytest.fixture
def tmp_envs_dir(tmp_path):
    return str(tmp_path)


def test_record_creates_log_file(tmp_envs_dir):
    record("write", "myapp", "staging", ["DB_URL"], envs_dir=tmp_envs_dir)
    assert os.path.exists(_audit_file_path(tmp_envs_dir))


def test_record_returns_entry(tmp_envs_dir):
    entry = record("write", "myapp", "staging", ["DB_URL", "SECRET"], envs_dir=tmp_envs_dir)
    assert entry.action == "write"
    assert entry.project == "myapp"
    assert entry.environment == "staging"
    assert entry.keys == ["DB_URL", "SECRET"]
    assert entry.detail is None


def test_record_with_detail(tmp_envs_dir):
    entry = record("delete", "myapp", "prod", ["OLD_KEY"], detail="removed deprecated key", envs_dir=tmp_envs_dir)
    assert entry.detail == "removed deprecated key"


def test_read_log_empty_when_no_file(tmp_envs_dir):
    entries = read_log(envs_dir=tmp_envs_dir)
    assert entries == []


def test_read_log_returns_all_entries(tmp_envs_dir):
    record("write", "app", "local", ["A"], envs_dir=tmp_envs_dir)
    record("delete", "app", "staging", ["B"], envs_dir=tmp_envs_dir)
    entries = read_log(envs_dir=tmp_envs_dir)
    assert len(entries) == 2


def test_read_log_filters_by_project(tmp_envs_dir):
    record("write", "app1", "local", ["X"], envs_dir=tmp_envs_dir)
    record("write", "app2", "local", ["Y"], envs_dir=tmp_envs_dir)
    entries = read_log(envs_dir=tmp_envs_dir, project="app1")
    assert len(entries) == 1
    assert entries[0].project == "app1"


def test_read_log_filters_by_environment(tmp_envs_dir):
    record("write", "app", "local", ["A"], envs_dir=tmp_envs_dir)
    record("write", "app", "prod", ["B"], envs_dir=tmp_envs_dir)
    entries = read_log(envs_dir=tmp_envs_dir, environment="prod")
    assert len(entries) == 1
    assert entries[0].environment == "prod"


def test_read_log_malformed_raises(tmp_envs_dir):
    audit_path = _audit_file_path(tmp_envs_dir)
    with open(audit_path, "w") as f:
        f.write("not valid json\n")
    with pytest.raises(AuditError):
        read_log(envs_dir=tmp_envs_dir)


def test_format_log_empty():
    result = format_log([])
    assert result == "No audit entries found."


def test_format_log_contains_fields(tmp_envs_dir):
    entry = record("write", "myapp", "staging", ["DB_URL"], detail="initial", envs_dir=tmp_envs_dir)
    output = format_log([entry])
    assert "write" in output
    assert "myapp/staging" in output
    assert "DB_URL" in output
    assert "initial" in output
