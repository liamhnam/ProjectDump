from __future__ import annotations

from pathlib import Path
from typing import Dict, Union

import pytest


def write_tree(root: Path, files: Dict[str, Union[str, bytes]]) -> Path:
    for rel, content in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content, encoding="utf-8")
    return root


@pytest.fixture
def make_project(tmp_path):
    def make(files: Dict[str, Union[str, bytes]], name: str = "demo") -> Path:
        return write_tree(tmp_path / name, files)

    return make
