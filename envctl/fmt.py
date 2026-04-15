"""Format environment variable sets for display or export."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Literal

FormatStyle = Literal["table", "dotenv", "json", "shell"]


class FmtError(Exception):
    """Raised when formatting fails."""


@dataclass
class FmtResult:
    project: str
    environment: str
    style: FormatStyle
    lines: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "environment": self.environment,
            "style": self.style,
            "output": self.rendered,
        }

    @property
    def rendered(self) -> str:
        return "\n".join(self.lines)


def _quote(value: str) -> str:
    return '"' + value.replace('"', '\\"') + '"'


def format_env(
    project: str,
    environment: str,
    variables: Dict[str, str],
    style: FormatStyle = "dotenv",
) -> FmtResult:
    """Format *variables* according to *style* and return a FmtResult."""
    if style not in ("table", "dotenv", "json", "shell"):
        raise FmtError(f"Unknown format style: {style!r}")

    lines: List[str] = []

    if style == "dotenv":
        for key, value in sorted(variables.items()):
            lines.append(f"{key}={_quote(value)}")

    elif style == "shell":
        for key, value in sorted(variables.items()):
            lines.append(f"export {key}={_quote(value)}")

    elif style == "json":
        import json
        lines.append(json.dumps(dict(sorted(variables.items())), indent=2))

    elif style == "table":
        if variables:
            col = max(len(k) for k in variables)
            lines.append(f"{'KEY':<{col}}  VALUE")
            lines.append("-" * (col + 2 + 20))
            for key in sorted(variables):
                lines.append(f"{key:<{col}}  {variables[key]}")
        else:
            lines.append("(no variables)")

    return FmtResult(project=project, environment=environment, style=style, lines=lines)
