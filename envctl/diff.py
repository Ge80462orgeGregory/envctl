"""Utilities for diffing environment variable sets between environments."""

from typing import Dict, Set, Tuple


DiffResult = Dict[str, dict]


def diff_envs(
    base: Dict[str, str],
    target: Dict[str, str],
) -> DiffResult:
    """Compare two env dicts and return a structured diff.

    Returns a dict with keys:
        - added:   keys present in target but not in base
        - removed: keys present in base but not in target
        - changed: keys present in both but with different values
        - unchanged: keys present in both with the same value
    """
    base_keys: Set[str] = set(base.keys())
    target_keys: Set[str] = set(target.keys())

    added = {k: target[k] for k in target_keys - base_keys}
    removed = {k: base[k] for k in base_keys - target_keys}

    changed: Dict[str, Tuple[str, str]] = {}
    unchanged: Dict[str, str] = {}

    for k in base_keys & target_keys:
        if base[k] != target[k]:
            changed[k] = {"from": base[k], "to": target[k]}
        else:
            unchanged[k] = base[k]

    return {
        "added": added,
        "removed": removed,
        "changed": changed,
        "unchanged": unchanged,
    }


def format_diff(result: DiffResult, mask_values: bool = True) -> str:
    """Render a DiffResult as a human-readable string.

    Args:
        result: Output of diff_envs().
        mask_values: If True, replace values with '***' for security.
    """
    lines = []

    def _val(v: str) -> str:
        return "***" if mask_values else v

    for k, v in sorted(result["added"].items()):
        lines.append(f"  + {k}={_val(v)}")

    for k, v in sorted(result["removed"].items()):
        lines.append(f"  - {k}={_val(v)}")

    for k, info in sorted(result["changed"].items()):
        from_val = _val(info["from"])
        to_val = _val(info["to"])
        lines.append(f"  ~ {k}: {from_val} -> {to_val}")

    if not lines:
        return "  (no differences)"

    summary = (
        f"  Added: {len(result['added'])}  "
        f"Removed: {len(result['removed'])}  "
        f"Changed: {len(result['changed'])}"
    )
    lines.append("")
    lines.append(summary)
    return "\n".join(lines)
