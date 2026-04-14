"""Tests for envctl.normalize."""

from __future__ import annotations

import pytest

from envctl.normalize import NormalizeError, NormalizeResult, normalize_env

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_store: dict[tuple[str, str], dict[str, str]] = {}


def _make_read(initial: dict[str, str], project: str = "proj", env: str = "dev"):
    _store[(project, env)] = dict(initial)

    def _read(p: str, e: str) -> dict[str, str]:
        return dict(_store.get((p, e), {}))

    return _read


_written: dict[tuple[str, str], dict[str, str]] = {}


def _write(p: str, e: str, variables: dict[str, str]) -> None:
    _written[(p, e)] = dict(variables)


def setup_function():
    _store.clear()
    _written.clear()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_normalize_uppercases_keys():
    read = _make_read({"db_host": "localhost", "db_port": "5432"})
    result = normalize_env("proj", "dev", read, _write)

    assert "db_host" in result.renamed
    assert result.renamed["db_host"] == "DB_HOST"
    assert "db_port" in result.renamed
    assert _written[("proj", "dev")] == {"DB_HOST": "localhost", "DB_PORT": "5432"}


def test_normalize_strips_value_whitespace():
    read = _make_read({"API_KEY": "  secret  ", "HOST": "localhost"})
    result = normalize_env("proj", "dev", read, _write)

    assert "API_KEY" in result.trimmed
    assert _written[("proj", "dev")]["API_KEY"] == "secret"
    assert _written[("proj", "dev")]["HOST"] == "localhost"


def test_normalize_skips_already_clean_keys():
    read = _make_read({"HOST": "localhost", "PORT": "8080"})
    result = normalize_env("proj", "dev", read, _write)

    assert "HOST" in result.skipped
    assert "PORT" in result.skipped
    assert result.total_changes == 0


def test_normalize_strip_values_false_leaves_whitespace():
    read = _make_read({"KEY": "  value  "})
    result = normalize_env("proj", "dev", read, _write, strip_values=False)

    assert _written[("proj", "dev")]["KEY"] == "  value  "
    assert result.trimmed == []


def test_normalize_custom_key_transform():
    read = _make_read({"MY_KEY": "val"})
    result = normalize_env(
        "proj", "dev", read, _write,
        key_transform=lambda k: k.lower(),
    )

    assert result.renamed["MY_KEY"] == "my_key"
    assert "my_key" in _written[("proj", "dev")]


def test_normalize_total_changes_counts_correctly():
    read = _make_read({"lower_key": "  spaced  ", "CLEAN": "ok"})
    result = normalize_env("proj", "dev", read, _write)

    # lower_key renamed -> LOWER_KEY (1 rename) + value trimmed (1 trim)
    assert result.total_changes == 2


def test_normalize_read_error_raises_normalize_error():
    def bad_read(p, e):
        raise RuntimeError("disk failure")

    with pytest.raises(NormalizeError, match="disk failure"):
        normalize_env("proj", "dev", bad_read, _write)


def test_normalize_write_error_raises_normalize_error():
    read = _make_read({"KEY": "value"})

    def bad_write(p, e, v):
        raise OSError("permission denied")

    with pytest.raises(NormalizeError, match="permission denied"):
        normalize_env("proj", "dev", read, bad_write)


def test_normalize_result_to_dict():
    read = _make_read({"key": "  val  "})
    result = normalize_env("proj", "dev", read, _write)
    d = result.to_dict()

    assert d["project"] == "proj"
    assert d["environment"] == "dev"
    assert isinstance(d["renamed"], dict)
    assert isinstance(d["trimmed"], list)
    assert isinstance(d["total_changes"], int)
