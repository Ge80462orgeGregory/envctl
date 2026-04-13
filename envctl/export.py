"""Export environment variables to different formats."""

import json
from typing import Dict, Optional


SUPPORTED_FORMATS = ("dotenv", "json", "shell")


class ExportError(Exception):
    """Raised when an export operation fails."""


def export_env(
    variables: Dict[str, str],
    fmt: str = "dotenv",
    prefix: Optional[str] = None,
) -> str:
    """Serialize *variables* to the requested format string.

    Args:
        variables: Mapping of variable names to values.
        fmt: One of ``dotenv``, ``json``, or ``shell``.
        prefix: Optional prefix prepended to every key.

    Returns:
        A string representation suitable for writing to a file or stdout.

    Raises:
        ExportError: If *fmt* is not supported.
    """
    if fmt not in SUPPORTED_FORMATS:
        raise ExportError(
            f"Unsupported format '{fmt}'. Choose from: {', '.join(SUPPORTED_FORMATS)}"
        )

    def _key(name: str) -> str:
        return f"{prefix}_{name}" if prefix else name

    if fmt == "json":
        return json.dumps({_key(k): v for k, v in variables.items()}, indent=2)

    lines = []
    for k, v in variables.items():
        key = _key(k)
        escaped = v.replace('"', '\\"')
        if fmt == "shell":
            lines.append(f'export {key}="{escaped}"')
        else:  # dotenv
            lines.append(f'{key}="{escaped}"')

    return "\n".join(lines)
