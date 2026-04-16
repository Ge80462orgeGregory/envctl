from typing import Optional
from envctl.env_store import read_env, write_env


class RenameKeyError(Exception):
    pass


class RenameKeyResult:
    def __init__(self, project: str, environment: str, old_key: str, new_key: str, value: str):
        self.project = project
        self.environment = environment
        self.old_key = old_key
        self.new_key = new_key
        self.value = value

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "environment": self.environment,
            "old_key": self.old_key,
            "new_key": self.new_key,
            "value": self.value,
        }


def rename_key(
    project: str,
    environment: str,
    old_key: str,
    new_key: str,
    read=read_env,
    write=write_env,
) -> RenameKeyResult:
    if not old_key:
        raise RenameKeyError("old_key must not be empty")
    if not new_key:
        raise RenameKeyError("new_key must not be empty")
    if old_key == new_key:
        raise RenameKeyError(f"old_key and new_key are the same: '{old_key}'")

    env = read(project, environment)

    if old_key not in env:
        raise RenameKeyError(f"Key '{old_key}' not found in {project}/{environment}")
    if new_key in env:
        raise RenameKeyError(f"Key '{new_key}' already exists in {project}/{environment}")

    value = env[old_key]
    updated = {k if k != old_key else new_key: v for k, v in env.items()}
    write(project, environment, updated)

    return RenameKeyResult(
        project=project,
        environment=environment,
        old_key=old_key,
        new_key=new_key,
        value=value,
    )
