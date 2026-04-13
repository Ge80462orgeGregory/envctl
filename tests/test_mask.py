"""Tests for envctl.mask module."""

import pytest
from envctl.mask import (
    MaskResult,
    _is_sensitive,
    _mask_value,
    mask_env,
    DEFAULT_SENSITIVE_PATTERNS,
    VISIBLE_CHARS,
)


# ---------------------------------------------------------------------------
# _is_sensitive
# ---------------------------------------------------------------------------

def test_sensitive_key_detected():
    assert _is_sensitive("DB_PASSWORD", DEFAULT_SENSITIVE_PATTERNS) is True


def test_non_sensitive_key_not_detected():
    assert _is_sensitive("APP_HOST", DEFAULT_SENSITIVE_PATTERNS) is False


def test_partial_match_in_key():
    assert _is_sensitive("STRIPE_API_KEY", DEFAULT_SENSITIVE_PATTERNS) is True


# ---------------------------------------------------------------------------
# _mask_value
# ---------------------------------------------------------------------------

def test_mask_value_hides_tail():
    result = _mask_value("supersecret", visible=4)
    assert result == "supe*******"


def test_mask_value_short_string():
    result = _mask_value("abc", visible=4)
    assert result == "***"


def test_mask_value_empty_string():
    assert _mask_value("", visible=4) == ""


def test_mask_value_exact_visible_length():
    result = _mask_value("abcd", visible=4)
    assert result == "****"


# ---------------------------------------------------------------------------
# mask_env
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_env():
    return {
        "APP_HOST": "localhost",
        "DB_PASSWORD": "hunter2",
        "API_KEY": "abcdef1234",
        "PORT": "8080",
        "SECRET_TOKEN": "topsecretvalue",
    }


def test_mask_env_returns_mask_result(sample_env):
    result = mask_env(sample_env)
    assert isinstance(result, MaskResult)


def test_mask_env_non_sensitive_unchanged(sample_env):
    result = mask_env(sample_env)
    assert result.masked["APP_HOST"] == "localhost"
    assert result.masked["PORT"] == "8080"


def test_mask_env_sensitive_keys_masked(sample_env):
    result = mask_env(sample_env)
    assert "hunter2" not in result.masked["DB_PASSWORD"]
    assert result.masked["DB_PASSWORD"].startswith("hunt")


def test_mask_env_api_key_masked(sample_env):
    result = mask_env(sample_env)
    assert result.masked["API_KEY"] != "abcdef1234"
    assert result.masked["API_KEY"].startswith("abcd")


def test_mask_env_total_masked_count(sample_env):
    result = mask_env(sample_env)
    assert result.total_masked == 3


def test_mask_env_masked_keys_sorted(sample_env):
    result = mask_env(sample_env)
    assert result.masked_keys == sorted(result.masked_keys)


def test_mask_env_extra_keys_always_masked():
    env = {"MY_CUSTOM_VAR": "should_be_masked", "NORMAL": "visible"}
    result = mask_env(env, extra_keys=["MY_CUSTOM_VAR"])
    assert "should_be_masked" not in result.masked["MY_CUSTOM_VAR"]
    assert result.masked["NORMAL"] == "visible"


def test_mask_env_custom_visible_chars():
    env = {"DB_PASSWORD": "abcdefgh"}
    result = mask_env(env, visible_chars=2)
    assert result.masked["DB_PASSWORD"] == "ab" + "*" * 6


def test_mask_env_original_preserved(sample_env):
    result = mask_env(sample_env)
    assert result.original == sample_env
