"""Walk a project and decide which files belong in the appendix.

Rules, in order:

1. ``exclude`` patterns from the config always win.
2. ``only`` (when set) restricts the result to matching paths.
3. Files matching ``include`` are taken even if .gitignore or the built-in
   exclusions would drop them, and even if they are not source code.
4. Otherwise a file must not be ignored by .gitignore, must not sit in a
   dependency/build folder, and must be a known source-code type.

All patterns use .gitignore syntax: ``*.json`` matches at any depth,
``src/**`` matches everything under ``src``, ``/build`` only at the root.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import pathspec

from . import languages
from .config import Config

# Folders that hold dependencies, caches, build output or tooling state.
DEFAULT_EXCLUDE_DIRS = frozenset(
    """
    .git .hg .svn .idea .vscode .vs .fleet .gradle .dart_tool .pub-cache .symlinks
    .next .nuxt .svelte-kit .angular .expo .turbo .parcel-cache .cache .output
    .vercel .netlify .serverless .terraform .docusaurus .yarn .pnpm-store
    node_modules bower_components jspm_packages vendor Pods Carthage DerivedData
    __pycache__ .mypy_cache .pytest_cache .ruff_cache .tox .nox .eggs .ipynb_checkpoints
    site-packages venv .venv virtualenv
    dist build out target obj bin coverage .nyc_output htmlcov ephemeral
    """.split()
)

# Files produced by code generators. Skipped when ``skip_generated`` is on.
GENERATED_PATTERNS = [
    "*.g.dart", "*.freezed.dart", "*.gr.dart", "*.mocks.dart", "*.config.dart",
    "GeneratedPluginRegistrant.*", "generated_plugin_registrant.*",
    "*.pb.go", "*.pb.cc", "*.pb.h", "*_pb2.py", "*_pb2_grpc.py", "*_pb2.pyi",
    "*.designer.cs", "*.Designer.cs", "*.g.cs", "*.g.i.cs", "AssemblyInfo.cs",
    "*.AssemblyInfo.cs", "*.generated.*", "next-env.d.ts", "R.java", "BuildConfig.java",
    # Build-tool wrapper scripts copied into every Gradle/Maven project.
    "gradlew", "gradlew.bat", "mvnw", "mvnw.cmd",
]

# Platform folders that Flutter / React Native scaffold and that app authors
# rarely touch. Skipped as boilerplate when ``default_excludes`` is on.
FLUTTER_PLATFORM_DIRS = frozenset({"android", "ios", "linux", "macos", "windows", "web"})
REACT_NATIVE_PLATFORM_DIRS = frozenset({"android", "ios"})
_FLUTTER_DEP = re.compile(r"^\s+flutter:\s*$|^\s+sdk:\s*flutter\s*$", re.MULTILINE)

# Well-known libraries that projects copy in instead of installing.
VENDORED_PATTERNS = [
    "jquery*.js", "bootstrap*.js", "bootstrap*.css", "popper*.js", "font-awesome*.css",
    "fontawesome*.css", "all.min.css", "chart*.umd.js", "swiper-bundle*", "aos.js", "aos.css",
]

# Bundled/minified assets. Skipped when ``skip_minified`` is on.
MINIFIED_PATTERNS = ["*.min.js", "*.min.mjs", "*.min.css", "*.bundle.js", "*.chunk.js"]

# Reasons a path is left out. The CLI translates these.
R_EXCLUDED = "excluded"          # matched an ``exclude`` pattern
R_NOT_ONLY = "not_only"          # outside the ``only`` patterns
R_GITIGNORE = "gitignore"
R_DEPENDENCY = "dependency"      # dependency / build / cache folder
R_HIDDEN = "hidden"              # dot-folder: .github, .devcontainer, ...
R_BOILERPLATE = "boilerplate"    # Flutter / React Native platform scaffolding
R_VENDORED = "vendored"          # third-party library copied into the project
R_NOT_SOURCE = "not_source"
R_BINARY = "binary"
R_GENERATED = "generated"
R_MINIFIED = "minified"
R_TOO_LARGE = "too_large"
R_OUTPUT = "output"              # the document being written
R_UNREADABLE = "unreadable"
R_EMPTY = "empty"


def spec(patterns: Iterable[str]) -> pathspec.PathSpec:
    return pathspec.GitIgnoreSpec.from_lines(list(patterns))


def natural_key(name: str) -> List:
    """Sort key where ``file2`` comes before ``file10``."""
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", name)]


@dataclass
class Candidate:
    rel: str            # POSIX path relative to the project root
    path: Path
    size: int
    explicit: bool      # matched an ``include`` pattern


@dataclass
class ScanResult:
    root: Path
    files: List[Candidate] = field(default_factory=list)
    skipped: List[Tuple[str, str]] = field(default_factory=list)  # (rel, reason)
    visible: List[str] = field(default_factory=list)  # for tree = "all"

    def counts(self) -> Dict[str, int]:
        out: Dict[str, int] = {}
        for _, reason in self.skipped:
            out[reason] = out.get(reason, 0) + 1
        return out


class _Ignore:
    """The .gitignore files in effect, deepest last (git's precedence)."""

    def __init__(self) -> None:
        self.layers: List[Tuple[str, pathspec.PathSpec]] = []

    def push(self, base: str, lines: List[str]) -> None:
        self.layers.append((base, spec(lines)))

    def ignored(self, rel: str, is_dir: bool) -> bool:
        result: Optional[bool] = None
        for base, layer in self.layers:
            if base:
                if not rel.startswith(base + "/"):
                    continue
                sub = rel[len(base) + 1:]
            else:
                sub = rel
            check = layer.check_file(sub + "/" if is_dir else sub)
            if check.include is not None:
                result = check.include
        return bool(result)


def _read_lines(path: Path) -> List[str]:
    try:
        return path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []


def _literal_segments(pattern: str) -> List[str]:
    return [s for s in pattern.strip("/").split("/") if s and not any(c in s for c in "*?[!")]


class Scanner:
    def __init__(self, root: Path, cfg: Config, output: Optional[Path] = None) -> None:
        self.root = root.resolve()
        self.cfg = cfg
        self.output = output.resolve() if output else None
        self.include = spec(cfg.include)
        self.exclude = spec(cfg.exclude)
        self.only = spec(cfg.only) if cfg.only else None
        self.generated = spec(GENERATED_PATTERNS)
        self.minified = spec(MINIFIED_PATTERNS)
        self.vendored = spec(VENDORED_PATTERNS)
        self.ignore = _Ignore()
        # Folder names that an ``include``/``only`` pattern spells out, e.g.
        # "build/generated/*.java" lets the scanner enter "build".
        self.reachable = {
            seg for p in [*cfg.include, *cfg.only] for seg in _literal_segments(p)
        }

    def scan(self) -> ScanResult:
        result = ScanResult(self.root)
        if self.cfg.use_gitignore:
            exclude_file = self.root / ".git" / "info" / "exclude"
            if exclude_file.is_file():
                self.ignore.push("", _read_lines(exclude_file))
        self._walk(self.root, "", result)
        if self.cfg.order:
            order_specs = [spec([p]) for p in self.cfg.order]

            def rank(c: Candidate) -> int:
                for i, s in enumerate(order_specs):
                    if s.match_file(c.rel):
                        return i
                return len(order_specs)

            result.files.sort(key=rank)  # stable: keeps tree order within a rank
        return result

    def _dir_reason(
        self, rel: str, name: str, path: Path, platform_dirs: frozenset
    ) -> Optional[str]:
        if self.exclude.match_file(rel + "/"):
            return R_EXCLUDED
        if name in self.reachable:
            return None
        if self.cfg.use_gitignore and self.ignore.ignored(rel, is_dir=True):
            return R_GITIGNORE
        if self.cfg.default_excludes:
            if (
                name in DEFAULT_EXCLUDE_DIRS
                or name.endswith(".egg-info")
                or (path / "pyvenv.cfg").is_file()  # a virtualenv under any name
            ):
                return R_DEPENDENCY
            if name.startswith("."):
                return R_HIDDEN
            if name in platform_dirs:
                return R_BOILERPLATE
        return None

    def _platform_dirs(self, directory: Path, file_names: List[str]) -> frozenset:
        """Scaffolded platform folders of a Flutter/React Native app root."""
        if not self.cfg.default_excludes:
            return frozenset()
        if "pubspec.yaml" in file_names:
            text = "\n".join(_read_lines(directory / "pubspec.yaml"))
            if _FLUTTER_DEP.search(text):
                return FLUTTER_PLATFORM_DIRS
        if "package.json" in file_names:
            text = "\n".join(_read_lines(directory / "package.json"))
            if '"react-native"' in text:
                return REACT_NATIVE_PLATFORM_DIRS
        return frozenset()

    def _file_reason(self, rel: str, name: str, path: Path, size: int) -> Tuple[Optional[str], bool]:
        """Return ``(reason to skip or None, explicitly included)``."""
        if self.output is not None and path.resolve() == self.output:
            return R_OUTPUT, False
        if self.exclude.match_file(rel):
            return R_EXCLUDED, False
        if self.only is not None and not self.only.match_file(rel):
            return R_NOT_ONLY, False
        if languages.is_binary_name(name):
            return R_BINARY, False
        explicit = self.include.match_file(rel)
        if not explicit:
            if self.cfg.use_gitignore and self.ignore.ignored(rel, is_dir=False):
                return R_GITIGNORE, False
            if languages.lookup(name) is None:
                return R_NOT_SOURCE, False
            if self.cfg.skip_generated and self.generated.match_file(rel):
                return R_GENERATED, False
            if self.cfg.skip_minified and self.minified.match_file(rel):
                return R_MINIFIED, False
            if self.cfg.default_excludes and self.vendored.match_file(rel):
                return R_VENDORED, False
        if size > self.cfg.max_file_kb * 1024:
            return R_TOO_LARGE, explicit
        if size == 0:
            return R_EMPTY, explicit
        return None, explicit

    def _walk(self, directory: Path, rel_dir: str, result: ScanResult) -> None:
        pushed = False
        if self.cfg.use_gitignore:
            gi = directory / ".gitignore"
            if gi.is_file():
                self.ignore.push(rel_dir, _read_lines(gi))
                pushed = True
        try:
            entries = list(os.scandir(directory))
        except OSError:
            result.skipped.append((rel_dir or ".", R_UNREADABLE))
            entries = []

        dirs, files = [], []
        for entry in entries:
            try:
                if entry.is_dir(follow_symlinks=False):
                    dirs.append(entry)
                elif entry.is_file():
                    files.append(entry)
            except OSError:
                continue
        dirs.sort(key=lambda e: natural_key(e.name))
        files.sort(key=lambda e: natural_key(e.name))
        platform_dirs = self._platform_dirs(directory, [e.name for e in files])

        for entry in dirs:
            rel = f"{rel_dir}/{entry.name}" if rel_dir else entry.name
            if entry.name == ".git":
                continue
            reason = self._dir_reason(rel, entry.name, Path(entry.path), platform_dirs)
            if reason:
                result.skipped.append((rel + "/", reason))
                continue
            self._walk(Path(entry.path), rel, result)

        for entry in files:
            rel = f"{rel_dir}/{entry.name}" if rel_dir else entry.name
            path = Path(entry.path)
            try:
                size = entry.stat().st_size
            except OSError:
                result.skipped.append((rel, R_UNREADABLE))
                continue
            reason, explicit = self._file_reason(rel, entry.name, path, size)
            if reason not in (R_GITIGNORE, R_EXCLUDED, R_OUTPUT, R_NOT_ONLY):
                result.visible.append(rel)
            if reason:
                result.skipped.append((rel, reason))
            else:
                result.files.append(Candidate(rel, path, size, explicit))

        if pushed:
            self.ignore.layers.pop()


def scan(root: Path, cfg: Config, output: Optional[Path] = None) -> ScanResult:
    return Scanner(root, cfg, output).scan()
