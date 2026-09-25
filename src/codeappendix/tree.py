"""Render a directory tree (``├──`` style) from a list of relative paths."""

from __future__ import annotations

from typing import Dict, Iterable, List

from .scanner import natural_key


def render(root_name: str, paths: Iterable[str]) -> List[str]:
    """Return the tree as lines, folders first, both sorted naturally."""
    tree: Dict[str, dict] = {}
    for path in paths:
        node = tree
        parts = path.split("/")
        for part in parts[:-1]:
            node = node.setdefault(part + "/", {})
        node.setdefault(parts[-1], None)

    lines = [root_name.rstrip("/") + "/"]

    def walk(node: Dict[str, dict], prefix: str) -> None:
        names = sorted(node, key=lambda n: (not n.endswith("/"), natural_key(n)))
        for i, name in enumerate(names):
            last = i == len(names) - 1
            lines.append(prefix + ("└── " if last else "├── ") + name)
            child = node[name]
            if child:
                walk(child, prefix + ("    " if last else "│   "))

    walk(tree, "")
    return lines
