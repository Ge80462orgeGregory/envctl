"""Tests for envctl.quota."""

from __future__ import annotations

import pytest

from envctl.quota import QuotaError, QuotaResult, check_quota


def _make_read(data: dict[str, dict[str, dict[str, str]]]):
    """Return a read_env stub backed by *data*."""

    def _read(project: str, environment: str) -> dict[str, str]:
        return data.get(project, {}).get(environment, {})

    return _read


_ENV = {
    "myapp": {
        "production": {f"KEY_{i}": str(i) for i in range(10)},  # 10 keys
        "staging": {f"KEY_{i}": str(i) for i in range(7)},     # 7 keys
        "local": {},                                              # 0 keys
    }
}

_read = _make_read(_ENV)


def test_result_is_quota_result():
    result = check_quota("myapp", "production", limit=20, read_env=_read)
    assert isinstance(result, QuotaResult)


def test_key_count_matches_env_size():
    result = check_quota("myapp", "production", limit=20, read_env=_read)
    assert result.key_count == 10


def test_not_exceeded_when_under_limit():
    result = check_quota("myapp", "production", limit=20, read_env=_read)
    assert result.exceeded is False


def test_exceeded_when_over_limit():
    result = check_quota("myapp", "production", limit=5, read_env=_read)
    assert result.exceeded is True


def test_exceeded_when_exactly_at_limit_plus_one():
    result = check_quota("myapp", "production", limit=9, read_env=_read)
    assert result.exceeded is True


def test_not_exceeded_when_exactly_at_limit():
    result = check_quota("myapp", "production", limit=10, read_env=_read)
    assert result.exceeded is False


def test_warning_raised_at_default_threshold():
    # 7 keys, limit=9 → 7/9 ≈ 77.8 % < 80 % → no warning
    result = check_quota("myapp", "staging", limit=9, read_env=_read)
    assert result.warning is False

    # 7 keys, limit=8 → 7/8 = 87.5 % ≥ 80 % → warning
    result = check_quota("myapp", "staging", limit=8, read_env=_read)
    assert result.warning is True


def test_warning_not_set_when_exceeded():
    result = check_quota("myapp", "production", limit=5, read_env=_read)
    assert result.exceeded is True
    assert result.warning is False


def test_custom_warn_at_threshold():
    # 10 keys, limit=20, warn_at=0.5 → 10/20 = 50 % ≥ 50 % → warning
    result = check_quota("myapp", "production", limit=20, warn_at=0.5, read_env=_read)
    assert result.warning is True


def test_empty_env_no_warning_no_exceeded():
    result = check_quota("myapp", "local", limit=10, read_env=_read)
    assert result.key_count == 0
    assert result.exceeded is False
    assert result.warning is False


def test_invalid_limit_raises_quota_error():
    with pytest.raises(QuotaError):
        check_quota("myapp", "production", limit=0, read_env=_read)


def test_negative_limit_raises_quota_error():
    with pytest.raises(QuotaError):
        check_quota("myapp", "production", limit=-1, read_env=_read)


def test_invalid_warn_at_raises_quota_error():
    with pytest.raises(QuotaError):
        check_quota("myapp", "production", limit=10, warn_at=0.0, read_env=_read)


def test_to_dict_contains_expected_keys():
    result = check_quota("myapp", "production", limit=20, read_env=_read)
    d = result.to_dict()
    assert set(d.keys()) == {"project", "environment", "key_count", "limit", "exceeded", "warning"}
    assert d["project"] == "myapp"
    assert d["environment"] == "production"
