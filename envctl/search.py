"""Search for keys or values across projects and environments."""

from dataclasses import dataclass, field
from typing import Optional

from envctl.env_store import list_projects, list_environments, read_env


@dataclass
class SearchMatch:
    project: str
    environment: str
    key: str
    value: str


@dataclass
class SearchResult:
    matches: list[SearchMatch] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.matches)


class SearchError(Exception):
    pass


def search_envs(
    query: str,
    *,
    project: Optional[str] = None,
    search_keys: bool = True,
    search_values: bool = True,
    case_sensitive: bool = False,
    read_fn=read_env,
    list_projects_fn=list_projects,
    list_environments_fn=list_environments,
) -> SearchResult:
    """Search for a query string across keys and/or values."""
    if not query:
        raise SearchError("Search query must not be empty.")
    if not search_keys and not search_values:
        raise SearchError("At least one of search_keys or search_values must be True.")

    needle = query if case_sensitive else query.lower()
    result = SearchResult()

    projects = [project] if project else list_projects_fn()

    for proj in projects:
        for env in list_environments_fn(proj):
            variables = read_fn(proj, env)
            for key, value in variables.items():
                haystack_key = key if case_sensitive else key.lower()
                haystack_val = value if case_sensitive else value.lower()
                matched = (search_keys and needle in haystack_key) or (
                    search_values and needle in haystack_val
                )
                if matched:
                    result.matches.append(
                        SearchMatch(project=proj, environment=env, key=key, value=value)
                    )

    return result


def format_search(result: SearchResult, *, show_values: bool = True) -> str:
    """Format a SearchResult for terminal output."""
    if result.total == 0:
        return "No matches found."

    lines = []
    current_group = None
    for match in sorted(
        result.matches, key=lambda m: (m.project, m.environment, m.key)
    ):
        group = f"{match.project} / {match.environment}"
        if group != current_group:
            lines.append(f"\n[{group}]")
            current_group = group
        if show_values:
            lines.append(f"  {match.key} = {match.value}")
        else:
            lines.append(f"  {match.key}")

    lines.append(f"\n{result.total} match(es) found.")
    return "\n".join(lines).strip()
