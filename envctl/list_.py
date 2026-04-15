"""List projects and environments stored in envctl."""

from dataclasses import dataclass, field
from typing import List, Optional

from envctl.env_store import list_projects, list_environments


@dataclass
class ListResult:
    project: Optional[str]
    entries: List[str] = field(default_factory=list)


class ListError(Exception):
    """Raised when listing fails."""


def list_all(envs_dir: str) -> List[ListResult]:
    """Return a ListResult per project, each containing its environments."""
    projects = list_projects(envs_dir)
    if not projects:
        return []

    results = []
    for project in sorted(projects):
        envs = sorted(list_environments(envs_dir, project))
        results.append(ListResult(project=project, entries=envs))
    return results


def list_project_envs(envs_dir: str, project: str) -> ListResult:
    """Return environments for a single project."""
    projects = list_projects(envs_dir)
    if project not in projects:
        raise ListError(f"Project '{project}' not found.")

    envs = sorted(list_environments(envs_dir, project))
    return ListResult(project=project, entries=envs)


def format_list(results: List[ListResult]) -> str:
    """Format list results as a human-readable string."""
    if not results:
        return "No projects found."

    lines = []
    for result in results:
        lines.append(f"[{result.project}]")
        if result.entries:
            for env in result.entries:
                lines.append(f"  - {env}")
        else:
            lines.append("  (no environments)")
    return "\n".join(lines)


def format_summary(results: List[ListResult]) -> str:
    """Format list results as a compact summary line.

    Example output:
        3 project(s), 7 environment(s) total.
    """
    if not results:
        return "No projects found."

    total_envs = sum(len(r.entries) for r in results)
    project_count = len(results)
    return (
        f"{project_count} project(s), {total_envs} environment(s) total."
    )
