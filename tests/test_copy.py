"""Tests for envctl.copy module."""

import pytest
from unittest.mock import patch, call
from envctl.copy import copy_env, CopyError


SRC_VARS = {"DB_HOST": "localhost", "DB_PORT": "5432", "SECRET": "abc123"}
DST_VARS = {"DB_HOST": "prod-host", "API_KEY": "xyz"}


def _make_read(src_vars, dst_vars):
    def _read(project, env):
        if env == "staging":
            return dict(src_vars)
        return dict(dst_vars)
    return _read


@patch("envctl.copy.write_env")
@patch("envctl.copy.read_env")
def test_copy_all_keys_no_overwrite(mock_read, mock_write):
    mock_read.side_effect = _make_read(SRC_VARS, DST_VARS)
    copied = copy_env("proj", "staging", "proj", "production", overwrite=False)
    # DB_HOST already exists in dst, should be skipped
    assert "DB_HOST" not in copied
    assert "DB_PORT" in copied
    assert "SECRET" in copied
    mock_write.assert_called_once()


@patch("envctl.copy.write_env")
@patch("envctl.copy.read_env")
def test_copy_all_keys_with_overwrite(mock_read, mock_write):
    mock_read.side_effect = _make_read(SRC_VARS, DST_VARS)
    copied = copy_env("proj", "staging", "proj", "production", overwrite=True)
    assert "DB_HOST" in copied
    assert copied["DB_HOST"] == "localhost"
    assert len(copied) == len(SRC_VARS)
    mock_write.assert_called_once()


@patch("envctl.copy.write_env")
@patch("envctl.copy.read_env")
def test_copy_specific_keys(mock_read, mock_write):
    mock_read.side_effect = _make_read(SRC_VARS, {})
    copied = copy_env("proj", "staging", "proj", "production", keys=["DB_PORT"])
    assert copied == {"DB_PORT": "5432"}


@patch("envctl.copy.write_env")
@patch("envctl.copy.read_env")
def test_copy_missing_key_raises(mock_read, mock_write):
    mock_read.side_effect = _make_read(SRC_VARS, {})
    with pytest.raises(CopyError, match="MISSING_KEY"):
        copy_env("proj", "staging", "proj", "production", keys=["MISSING_KEY"])
    mock_write.assert_not_called()


@patch("envctl.copy.write_env")
@patch("envctl.copy.read_env")
def test_copy_empty_source_raises(mock_read, mock_write):
    mock_read.return_value = {}
    with pytest.raises(CopyError, match="empty or does not exist"):
        copy_env("proj", "staging", "proj", "production")
    mock_write.assert_not_called()


@patch("envctl.copy.write_env")
@patch("envctl.copy.read_env")
def test_copy_nothing_to_copy_skips_write(mock_read, mock_write):
    # All source keys already exist in destination, no overwrite
    same_vars = {"KEY": "value"}
    mock_read.side_effect = _make_read(same_vars, same_vars)
    copied = copy_env("proj", "staging", "proj", "production", overwrite=False)
    assert copied == {}
    mock_write.assert_not_called()
