"""Swap the values of two keys within an environment."""
from dataclasses import dataclass
from typing import Callable, Dict


class SwapError(Exception):
    pass


@dataclass
class SwapResult:
    project: str
    environment: str
    key_a: str
    key_b: str
    value_a: str
    value_b: str

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "environment": self.environment,
            "key_a": self.key_a,
            "key_b": self.key_b,
            "value_a": self.value_a,
            "value_b": self.value_b,
        }


def swap_keys(
    project: str,
    environment: str,
    key_a: str,
    key_b: str,
    read_env: Callable[[str, str], Dict[str, str]],
    write_env: Callable[[str, str, Dict[str, str]], None],
) -> SwapResult:
    """Swap the values of key_a and key_b in the given environment."""
    if key_a == key_b:
        raise SwapError(f"Cannot swap a key with itself: '{key_a}'")

    env = read_env(project, environment)

    if key_a not in env:
        raise SwapError(f"Key '{key_a}' not found in {project}/{environment}")
    if key_b not in env:
        raise SwapError(f"Key '{key_b}' not found in {project}/{environment}")

    val_a = env[key_a]
    val_b = env[key_b]

    env[key_a] = val_b
    env[key_b] = val_a

    write_env(project, environment, env)

    return SwapResult(
        project=project,
        environment=environment,
        key_a=key_a,
        key_b=key_b,
        value_a=val_a,
        value_b=val_b,
    )
