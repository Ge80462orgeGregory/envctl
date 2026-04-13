"""Import environment variables from a .env or JSON file into an env store."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

from envctl.env_store import read_env, write_env


class ImportError(Exception):  # noqa: A001
    """Raised when an import operation fails."""


def _parse_dotenv(text: str) -> Dict[str, str]:
    """Parse a .env-formatted string into a key/value dict."""
    result: Dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            result[key] = value
    return result


def _parse_json(text: str) -> Dict[str, str]:
    """Parse a JSON object into a key/value dict (all values coerced to str)."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ImportError(f"Invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ImportError("JSON root must be an object.")
    return {str(k): str(v) for k, v in data.items()}


def import_env(
    project: str,
    environment: str,
    source: Path,
    fmt: str = "dotenv",
    overwrite: bool = False,
    prefix: Optional[str] = None,
) -> Dict[str, str]:
    """Import variables from *source* into the given project/environment.

    Returns a dict of keys that were actually written (new or updated).
    """
    if not source.exists():
        raise ImportError(f"Source file not found: {source}")

    text = source.read_text(encoding="utf-8")

    if fmt == "dotenv":
        incoming = _parse_dotenv(text)
    elif fmt == "json":
        incoming = _parse_json(text)
    else:
        raise ImportError(f"Unsupported format: {fmt!r}. Use 'dotenv' or 'json'.")

    if not incoming:
        return {}

    if prefix:
        incoming = {f"{prefix}{k}": v for k, v in incoming.items()}

    existing = read_env(project, environment)
    merged = dict(existing)
    written: Dict[str, str] = {}

    for key, value in incoming.items():
        if key in existing and existing[key] == value:
            continue
        if key in existing and not overwrite:
            continue
        merged[key] = value
        written[key] = value

    if written:
        write_env(project, environment, merged)

    return written
