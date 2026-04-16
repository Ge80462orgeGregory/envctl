"""Check that required keys are present in an environment."""
from dataclasses import dataclass, field
from typing import List, Dict


class RequiredError(Exception):
    pass


@dataclass
class RequiredResult:
    project: str
    environment: str
    required: List[str]
    missing: List[str]
    present: List[str]

    def to_dict(self) -> Dict:
        return {
            "project": self.project,
            "environment": self.environment,
            "required": self.required,
            "missing": self.missing,
            "present": self.present,
            "satisfied": self.satisfied,
        }

    @property
    def satisfied(self) -> bool:
        return len(self.missing) == 0


def check_required(
    project: str,
    environment: str,
    required_keys: List[str],
    read_env,
) -> RequiredResult:
    if not required_keys:
        raise RequiredError("No required keys specified.")

    env = read_env(project, environment)
    if env is None:
        raise RequiredError(f"Environment '{environment}' not found in project '{project}'.")

    present = [k for k in required_keys if k in env and env[k] != ""]
    missing = [k for k in required_keys if k not in present]

    return RequiredResult(
        project=project,
        environment=environment,
        required=list(required_keys),
        missing=missing,
        present=present,
    )
