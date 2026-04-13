"""Pin specific environment variable keys to prevent them from being overwritten."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


class PinError(Exception):
    pass


@dataclass
class PinResult:
    project: str
    environment: str
    pinned: list[str] = field(default_factory=list)
    unpinned: list[str] = field(default_factory=list)
    already_pinned: list[str] = field(default_factory=list)
    not_pinned: list[str] = field(default_factory=list)


_PINS_KEY = "__pinned__"


def _get_pins(read: Callable, project: str, environment: str) -> list[str]:
    data = read(project, environment)
    raw = data.get(_PINS_KEY, "")
    return [k.strip() for k in raw.split(",") if k.strip()] if raw else []


def _set_pins(
    read: Callable,
    write: Callable,
    project: str,
    environment: str,
    pins: list[str],
) -> None:
    data = read(project, environment)
    if pins:
        data[_PINS_KEY] = ",".join(sorted(set(pins)))
    else:
        data.pop(_PINS_KEY, None)
    write(project, environment, data)


def pin_keys(
    project: str,
    environment: str,
    keys: list[str],
    read: Callable,
    write: Callable,
) -> PinResult:
    result = PinResult(project=project, environment=environment)
    env_data = read(project, environment)
    existing_pins = _get_pins(read, project, environment)

    for key in keys:
        if key not in env_data and key != _PINS_KEY:
            raise PinError(f"Key '{key}' does not exist in {project}/{environment}")
        if key in existing_pins:
            result.already_pinned.append(key)
        else:
            result.pinned.append(key)

    new_pins = list(set(existing_pins) | set(result.pinned))
    _set_pins(read, write, project, environment, new_pins)
    return result


def unpin_keys(
    project: str,
    environment: str,
    keys: list[str],
    read: Callable,
    write: Callable,
) -> PinResult:
    result = PinResult(project=project, environment=environment)
    existing_pins = _get_pins(read, project, environment)

    for key in keys:
        if key in existing_pins:
            result.unpinned.append(key)
        else:
            result.not_pinned.append(key)

    new_pins = [p for p in existing_pins if p not in result.unpinned]
    _set_pins(read, write, project, environment, new_pins)
    return result


def get_pinned_keys(
    project: str,
    environment: str,
    read: Callable,
) -> list[str]:
    return _get_pins(read, project, environment)


def is_pinned(key: str, project: str, environment: str, read: Callable) -> bool:
    return key in _get_pins(read, project, environment)
