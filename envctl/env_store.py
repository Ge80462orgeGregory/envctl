"""Environment variable store for envctl.

Provides read/write access to per-project, per-environment
.env files stored under the envctl config directory.
"""

from pathlib import Path
from typing import Optional

from envctl.config import get_envs_dir, load_config


def _env_file_path(project: str, environment: str, envs_dir: Optional[Path] = None) -> Path:
    """Return the path to a specific project+environment .env file."""
    if envs_dir is None:
        envs_dir = get_envs_dir()
    return envs_dir / project / f"{environment}.env"


def list_projects() -> list[str]:
    """Return all project names that have stored environments."""
    envs_dir = get_envs_dir()
    if not envs_dir.exists():
        return []
    return [d.name for d in envs_dir.iterdir() if d.is_dir()]


def list_environments(project: str) -> list[str]:
    """Return all stored environment names for a given project."""
    envs_dir = get_envs_dir()
    project_dir = envs_dir / project
    if not project_dir.exists():
        return []
    return [f.stem for f in project_dir.glob("*.env")]


def read_env(project: str, environment: str) -> dict[str, str]:
    """Read and parse an .env file into a dictionary."""
    path = _env_file_path(project, environment)
    if not path.exists():
        return {}
    env_vars: dict[str, str] = {}
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                env_vars[key.strip()] = value.strip()
    return env_vars


def write_env(project: str, environment: str, variables: dict[str, str]) -> Path:
    """Write a dictionary of variables to an .env file. Returns the file path."""
    path = _env_file_path(project, environment)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        f.write(f"# envctl managed — project={project} env={environment}\n")
        for key, value in sorted(variables.items()):
            f.write(f"{key}={value}\n")
    return path


def delete_env(project: str, environment: str) -> bool:
    """Delete a stored environment file. Returns True if deleted."""
    path = _env_file_path(project, environment)
    if path.exists():
        path.unlink()
        return True
    return False
