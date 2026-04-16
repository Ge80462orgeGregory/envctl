from dataclasses import dataclass, field
from typing import Dict, List


TYPE_PATTERNS = {
    "int": lambda v: v.lstrip("-").isdigit(),
    "float": lambda v: _is_float(v),
    "bool": lambda v: v.lower() in ("true", "false", "1", "0", "yes", "no"),
    "url": lambda v: v.startswith(("http://", "https://")),
    "email": lambda v: "@" in v and "." in v.split("@")[-1],
}


def _is_float(v: str) -> bool:
    try:
        float(v)
        return True
    except ValueError:
        return False


@dataclass
class TypeIssue:
    key: str
    value: str
    expected_type: str
    actual_inferred: str

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "value": self.value,
            "expected_type": self.expected_type,
            "actual_inferred": self.actual_inferred,
        }


@dataclass
class TypeCheckResult:
    project: str
    environment: str
    issues: List[TypeIssue] = field(default_factory=list)
    checked: int = 0

    @property
    def passed(self) -> bool:
        return len(self.issues) == 0

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "environment": self.environment,
            "checked": self.checked,
            "passed": self.passed,
            "issues": [i.to_dict() for i in self.issues],
        }


class TypeCheckError(Exception):
    pass


def infer_type(value: str) -> str:
    for type_name, check in TYPE_PATTERNS.items():
        if check(value):
            return type_name
    return "string"


def typecheck_env(
    project: str,
    environment: str,
    schema: Dict[str, str],
    read_env,
) -> TypeCheckResult:
    env = read_env(project, environment)
    if env is None:
        raise TypeCheckError(f"Environment '{environment}' not found in project '{project}'")

    issues = []
    checked = 0

    for key, expected_type in schema.items():
        if key not in env:
            continue
        checked += 1
        value = env[key]
        inferred = infer_type(value)
        if expected_type not in TYPE_PATTERNS:
            raise TypeCheckError(f"Unknown type '{expected_type}' in schema for key '{key}'")
        if not TYPE_PATTERNS[expected_type](value):
            issues.append(TypeIssue(
                key=key,
                value=value,
                expected_type=expected_type,
                actual_inferred=inferred,
            ))

    return TypeCheckResult(
        project=project,
        environment=environment,
        issues=issues,
        checked=checked,
    )
