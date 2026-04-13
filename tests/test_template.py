"""Tests for envctl.template."""

from __future__ import annotations

import pytest

from envctl.template import TemplateError, TemplateResult, render_template


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_read(data: dict[str, str]):
    """Return a read_env stub that always returns *data*."""
    def _read(project: str, environment: str) -> dict[str, str]:
        return dict(data)
    return _read


# ---------------------------------------------------------------------------
# Basic substitution
# ---------------------------------------------------------------------------

def test_single_placeholder_substituted():
    result = render_template(
        "Hello, {{NAME}}!",
        _make_read({"NAME": "world"}),
        "myapp", "dev",
    )
    assert result.rendered == "Hello, world!"
    assert result.substituted == ["NAME"]
    assert result.missing == []


def test_multiple_placeholders_substituted():
    tmpl = "{{HOST}}:{{PORT}}"
    result = render_template(
        tmpl,
        _make_read({"HOST": "localhost", "PORT": "5432"}),
        "myapp", "dev",
    )
    assert result.rendered == "localhost:5432"
    assert set(result.substituted) == {"HOST", "PORT"}


def test_placeholder_with_spaces():
    """Spaces around key name inside braces should be tolerated."""
    result = render_template(
        "{{ DB_URL }}",
        _make_read({"DB_URL": "postgres://localhost/db"}),
        "myapp", "prod",
    )
    assert result.rendered == "postgres://localhost/db"


def test_missing_placeholder_left_intact():
    result = render_template(
        "value={{MISSING}}",
        _make_read({}),
        "myapp", "dev",
    )
    assert result.rendered == "value={{MISSING}}"
    assert result.missing == ["MISSING"]
    assert result.total_missing == 1


def test_duplicate_placeholder_counted_once():
    result = render_template(
        "{{X}} and {{X}}",
        _make_read({"X": "42"}),
        "myapp", "dev",
    )
    assert result.rendered == "42 and 42"
    assert result.substituted == ["X"]  # deduplicated
    assert result.total_substituted == 1


def test_no_placeholders_returns_template_unchanged():
    tmpl = "no placeholders here"
    result = render_template(tmpl, _make_read({"A": "1"}), "p", "e")
    assert result.rendered == tmpl
    assert result.substituted == []
    assert result.missing == []


# ---------------------------------------------------------------------------
# Strict mode
# ---------------------------------------------------------------------------

def test_strict_raises_on_missing_key():
    with pytest.raises(TemplateError, match="MISSING"):
        render_template(
            "{{MISSING}}",
            _make_read({}),
            "myapp", "dev",
            strict=True,
        )


def test_strict_raises_when_env_empty():
    with pytest.raises(TemplateError):
        render_template(
            "{{KEY}}",
            _make_read({}),
            "myapp", "dev",
            strict=True,
        )


def test_strict_succeeds_when_all_keys_present():
    result = render_template(
        "{{A}}-{{B}}",
        _make_read({"A": "foo", "B": "bar"}),
        "myapp", "prod",
        strict=True,
    )
    assert result.rendered == "foo-bar"
    assert result.missing == []
