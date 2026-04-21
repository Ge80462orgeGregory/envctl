"""Base64 encode/decode values in an environment set."""

from __future__ import annotations

import base64
from dataclasses import dataclass, field
from typing import Callable

from envctl.env_store import read_env, write_env


class EncodeError(Exception):
    pass


@dataclass
class EncodeResult:
    project: str
    environment: str
    encoded: list[str] = field(default_factory=list)
    decoded: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)

    @property
    def total_changed(self) -> int:
        return len(self.encoded) + len(self.decoded)

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "environment": self.environment,
            "encoded": self.encoded,
            "decoded": self.decoded,
            "skipped": self.skipped,
            "total_changed": self.total_changed,
        }


def _b64_encode(value: str) -> str:
    return base64.b64encode(value.encode()).decode()


def _b64_decode(value: str) -> str:
    try:
        return base64.b64decode(value.encode()).decode()
    except Exception as exc:
        raise EncodeError(f"Invalid base64 value: {value!r}") from exc


def encode_env(
    project: str,
    environment: str,
    keys: list[str] | None = None,
    *,
    decode: bool = False,
    read: Callable = read_env,
    write: Callable = write_env,
) -> EncodeResult:
    """Base64-encode (or decode) values for the given keys.

    If *keys* is None every key in the environment is processed.
    """
    variables = read(project, environment)
    if not variables:
        raise EncodeError(
            f"Environment '{environment}' in project '{project}' is empty or does not exist."
        )

    target_keys = keys if keys is not None else list(variables.keys())
    unknown = [k for k in target_keys if k not in variables]
    if unknown:
        raise EncodeError(f"Keys not found: {', '.join(unknown)}")

    result = EncodeResult(project=project, environment=environment)
    updated = dict(variables)

    transform: Callable[[str], str] = _b64_decode if decode else _b64_encode

    for key in target_keys:
        original = variables[key]
        try:
            new_value = transform(original)
        except EncodeError:
            result.skipped.append(key)
            continue

        if new_value == original:
            result.skipped.append(key)
        else:
            updated[key] = new_value
            if decode:
                result.decoded.append(key)
            else:
                result.encoded.append(key)

    write(project, environment, updated)
    return result
