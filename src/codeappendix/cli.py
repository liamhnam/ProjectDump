"""Command-line interface: ``codeappendix [build|list|init] [PATH] [options]``."""

from __future__ import annotations

import argparse
import sys
import re
import time
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from . import __version__
from .config import (
    CHOICES,
    CONFIG_FILENAME,
    DEFAULT_PRESET,
    PRESETS,
    Config,
    ConfigError,
    apply,
    render_template,
    resolve,
)
from .i18n import fmt_int, t

COMMANDS = ("build", "list", "init")

# Order in which skip reasons are reported.
REASON_ORDER = (
    "dependency", "boilerplate", "hidden", "gitignore", "not_source", "vendored", "generated", "minified", "binary",
    "too_large", "empty", "unreadable", "excluded", "not_only", "output",
)


def _add_common(p: argparse.ArgumentParser) -> None:
    p.add_argument("path", nargs="?", default=".", help="project folder (default: current folder)")
    p.add_argument("-c", "--config", type=Path, help=f"config file (default: PATH/{CONFIG_FILENAME} if present)")
    p.add_argument("-p", "--preset", choices=sorted(PRESETS), help=f"layout preset (default: {DEFAULT_PRESET})")
    p.add_argument("--lang", choices=CHOICES["language"], dest="language", help="language of document labels and messages")

    f = p.add_argument_group("file selection (patterns use .gitignore syntax)")
    f.add_argument("-i", "--include", action="append", default=[], metavar="GLOB",
                   help="also include matching files, e.g. '*.json' (repeatable)")
    f.add_argument("-x", "--exclude", action="append", default=[], metavar="GLOB",
                   help="leave out matching files/folders, e.g. 'tests/' (repeatable)")
    f.add_argument("--only", action="append", default=[], metavar="GLOB",
                   help="take only matching files, e.g. 'src/**' (repeatable)")
    f.add_argument("--order", action="append", default=[], metavar="GLOB",
                   help="put matching files first, in the order given (repeatable)")
    f.add_argument("--no-gitignore", action="store_false", dest="use_gitignore", default=None,
                   help="do not honour .gitignore files")
    f.add_argument("--no-default-excludes", action="store_false", dest="default_excludes", default=None,
                   help="also scan node_modules, venv, build, dist, ...")
    f.add_argument("--keep-generated", action="store_false", dest="skip_generated", default=None,
                   help="keep files that look machine-generated")
    f.add_argument("--keep-minified", action="store_false", dest="skip_minified", default=None,
                   help="keep minified files")
    f.add_argument("--max-file-kb", type=int, metavar="KB", help="skip files larger than this (default 1024)")

    d = p.add_argument_group("document")
    d.add_argument("--title", help="appendix title (default: 'PHỤ LỤC A. MÃ NGUỒN CHƯƠNG TRÌNH')")
    d.add_argument("--label", help="appendix letter used for numbering, '' for none (default: A)")
    d.add_argument("--name", dest="project_name", help="project name used in the introduction")
    d.add_argument("--tree", choices=CHOICES["tree"], help="directory tree: included files, all files, or none")
    d.add_argument("--no-summary", action="store_false", dest="summary_table", default=None,
                   help="omit the file list table")
    d.add_argument("--no-file-info", action="store_false", dest="file_info", default=None,
                   help="omit the 'language · lines' line under each file name")
    d.add_argument("--plain-headings", action="store_const", const="plain", dest="file_heading",
                   help="file names are bold text, not headings (keeps them out of the thesis TOC)")
    d.add_argument("--page-break", action="store_true", dest="page_break_per_file", default=None,
                   help="start every file on a new page")
    d.add_argument("--page-size", choices=CHOICES["page_size"])

    c = p.add_argument_group("code")
    c.add_argument("--highlight", choices=CHOICES["highlight"],
                   help="color, mono (black-and-white printing) or none")
    c.add_argument("--theme", help="Pygments colour theme (default: vs)")
    c.add_argument("--no-line-numbers", action="store_false", dest="line_numbers", default=None)
    c.add_argument("--code-font", help="monospaced font (default: Consolas)")
    c.add_argument("--code-size", type=float, metavar="PT", help="code font size (default: 10)")
    c.add_argument("--font", help="text font (default: Times New Roman)")
    c.add_argument("--font-size", type=float, metavar="PT", help="text font size (default: 13)")
    c.add_argument("--max-lines", type=int, metavar="N",
                   help="show at most N lines per file (beginning and end); 0 = no limit")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="codeappendix",
        description="Turn a project's source code into a formatted Word appendix (.docx).",
        epilog="Examples:\n"
               "  codeappendix .                      # build ./<folder>-ma-nguon.docx\n"
               "  codeappendix list . --verbose       # preview which files are taken\n"
               "  codeappendix . --pdf -x 'tests/'    # also export a PDF, without tests\n"
               "  codeappendix init .                 # write a codeappendix.toml to edit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command")

    b = sub.add_parser("build", help="create the .docx (default command)")
    _add_common(b)
    b.add_argument("-o", "--output", type=Path, help="output .docx path (default: ./<folder>-ma-nguon.docx)")
    b.add_argument("--pdf", action="store_true", help="also export a PDF (needs LibreOffice)")
    b.add_argument("-q", "--quiet", action="store_true", help="print only errors")

    ls = sub.add_parser("list", help="show which files would be included, without writing anything")
    _add_common(ls)
    ls.add_argument("-v", "--verbose", action="store_true", help="list every skipped file")

    ini = sub.add_parser("init", help=f"write a commented {CONFIG_FILENAME} into the project")
    ini.add_argument("path", nargs="?", default=".")
    ini.add_argument("-p", "--preset", choices=sorted(PRESETS), default=DEFAULT_PRESET)
    ini.add_argument("--force", action="store_true", help="overwrite an existing file")
    ini.add_argument("--lang", choices=CHOICES["language"], dest="language", default="vi")
    return parser


_SCALAR_KEYS = (
    "language", "title", "label", "project_name", "tree", "summary_table", "file_info",
    "file_heading", "page_break_per_file", "page_size", "highlight", "theme",
    "line_numbers", "code_font", "code_size", "font", "font_size", "max_lines",
    "use_gitignore", "default_excludes", "skip_generated", "skip_minified", "max_file_kb",
)
_LIST_KEYS = ("include", "exclude", "only", "order")


def load_config(args: argparse.Namespace, project: Path) -> tuple:
    overrides: Dict[str, Any] = {
        k: getattr(args, k) for k in _SCALAR_KEYS if getattr(args, k, None) is not None
    }
    cfg, used = resolve(project, args.config, args.preset, overrides)
    extend = {k: getattr(cfg, k) + getattr(args, k) for k in _LIST_KEYS if getattr(args, k)}
    if extend:
        cfg = apply(cfg, extend)
    if not cfg.project_name:
        cfg = apply(cfg, {"project_name": project.name or str(project)})
    return cfg, used


def slug(name: str) -> str:
    ascii_name = unicodedata.normalize("NFKD", name.replace("đ", "d").replace("Đ", "D"))
    ascii_name = ascii_name.encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9]+", "-", ascii_name).strip("-").lower() or "project"


def default_output(project: Path, cfg: Config) -> Path:
    suffix = "source-code" if cfg.language == "en" else "ma-nguon"
    return Path.cwd() / f"{slug(project.name or 'project')}-{suffix}.docx"


def skipped_summary(lang: str, counts: Dict[str, int]) -> str:
    parts = [
        f"{t(lang, 'reason_' + r)} {fmt_int(lang, counts[r])}"
        for r in REASON_ORDER if counts.get(r)
    ]
    return ", ".join(parts)


class Printer:
    def __init__(self, quiet: bool = False) -> None:
        self.quiet = quiet

    def __call__(self, *args: Any) -> None:
        if not self.quiet:
            print(*args)


def _collect(args, project: Path, output: Optional[Path]):
    from .reader import load_all
    from .scanner import scan
    from .tree import render

    cfg, used = load_config(args, project)
    result = scan(project, cfg, output)
    files = load_all(result, cfg)
    root_name = project.name or str(project)
    tree_lines: Optional[List[str]] = None
    if cfg.tree == "included":
        tree_lines = render(root_name, [f.rel for f in files])
    elif cfg.tree == "all":
        tree_lines = render(root_name, result.visible)
    return cfg, used, result, files, tree_lines


def cmd_build(args) -> int:
    from .docx_writer import DocxBuilder, estimate_pages

    project = Path(args.path).expanduser().resolve()
    lang_hint = args.language or "vi"
    if not project.is_dir():
        print(t(lang_hint, "not_a_dir", path=args.path), file=sys.stderr)
        return 1
    output = args.output.expanduser().resolve() if args.output else None
    cfg, used, result, files, tree_lines = _collect(args, project, output)
    lang = cfg.language
    out = Printer(args.quiet)
    out(t(lang, "scanning", path=project))
    if used:
        out(t(lang, "config_used", path=used))
    if not files:
        print(t(lang, "no_files", path=args.path), file=sys.stderr)
        return 1

    output = output or default_output(project, cfg)
    if output.suffix.lower() != ".docx":
        output = output.with_suffix(output.suffix + ".docx") if output.suffix else output.with_suffix(".docx")
    output.parent.mkdir(parents=True, exist_ok=True)

    out(t(lang, "writing"))
    started = time.monotonic()
    builder = DocxBuilder(cfg, cfg.project_name)
    builder.build(files, tree_lines)
    try:
        builder.save(output)
    except OSError as exc:
        print(t(lang, "write_failed", path=output, error=exc.strerror or exc), file=sys.stderr)
        return 1

    total = sum(f.total_lines for f in files)
    pages = estimate_pages(cfg, files, tree_lines)
    out(t(lang, "written", path=output) + f"  ({time.monotonic() - started:.1f}s)")
    out("  " + t(lang, "stats", files=fmt_int(lang, len(files)), lines=fmt_int(lang, total),
                 pages=fmt_int(lang, pages)))
    summary = skipped_summary(lang, result.counts())
    if summary:
        out("  " + t(lang, "skipped_summary", details=summary))

    if args.pdf:
        from .pdf import PdfError, convert, count_pages, find_soffice

        soffice = find_soffice()
        if not soffice:
            print(t(lang, "pdf_missing"), file=sys.stderr)
            return 1
        try:
            pdf = convert(output, soffice)
        except PdfError as exc:
            print(t(lang, "pdf_failed", error=exc), file=sys.stderr)
            return 1
        n = count_pages(pdf)
        out(t(lang, "pdf_written", path=pdf, pages=n) if n else t(lang, "pdf_written_nopages", path=pdf))
    if cfg.summary_table:
        out(t(lang, "open_in_word"))
    return 0


def cmd_list(args) -> int:
    from .docx_writer import estimate_pages

    project = Path(args.path).expanduser().resolve()
    if not project.is_dir():
        print(t(args.language or "vi", "not_a_dir", path=args.path), file=sys.stderr)
        return 1
    cfg, used, result, files, tree_lines = _collect(args, project, None)
    lang = cfg.language
    if used:
        print(t(lang, "config_used", path=used))
    print(t(lang, "list_header"))
    width = max((len(f.rel) for f in files), default=10)
    lang_width = max((len(f.language) for f in files), default=8)
    num_width = len(str(len(files)))
    for i, f in enumerate(files, start=1):
        lines = fmt_int(lang, f.total_lines)
        note = f" → {fmt_int(lang, len(f.lines))}" if f.omitted else ""
        print(f"  {str(i).rjust(num_width)}. {f.rel.ljust(width)}  {f.language.ljust(lang_width)}  "
              f"{lines.rjust(7)} {t(lang, 'lines_unit')}{note}")
    total = sum(f.total_lines for f in files)
    print()
    print(t(lang, "stats", files=fmt_int(lang, len(files)), lines=fmt_int(lang, total),
            pages=fmt_int(lang, estimate_pages(cfg, files, tree_lines) if files else 0)))

    if result.skipped:
        print()
        print(t(lang, "list_skipped"))
        counts = result.counts()
        by_reason: Dict[str, List[str]] = {}
        for rel, reason in result.skipped:
            by_reason.setdefault(reason, []).append(rel)
        for reason in REASON_ORDER:
            items = by_reason.get(reason)
            if not items:
                continue
            label = f"{t(lang, 'reason_' + reason)} ({fmt_int(lang, counts[reason])})"
            if args.verbose:
                print(f"  {label}:")
                for rel in items:
                    print(f"      {rel}")
            else:
                preview = ", ".join(items[:4]) + (", …" if len(items) > 4 else "")
                print(f"  {label}: {preview}")
        if not args.verbose:
            print(t(lang, "list_hint"))
    return 0 if files else 1


def cmd_init(args) -> int:
    project = Path(args.path).expanduser().resolve()
    lang = args.language
    if not project.is_dir():
        print(t(lang, "not_a_dir", path=args.path), file=sys.stderr)
        return 1
    target = project / CONFIG_FILENAME
    if target.exists() and not args.force:
        print(t(lang, "init_exists", path=target), file=sys.stderr)
        return 1
    target.write_text(render_template(args.preset), encoding="utf-8")
    print(t(lang, "init_written", path=target))
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="replace")  # type: ignore[attr-defined]
        except (AttributeError, ValueError):
            pass
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or (argv[0] not in COMMANDS and argv[0] not in ("-h", "--help", "--version")):
        argv.insert(0, "build")
    args = build_parser().parse_args(argv)
    try:
        if args.command == "list":
            return cmd_list(args)
        if args.command == "init":
            return cmd_init(args)
        return cmd_build(args)
    except ConfigError as exc:
        print(f"codeappendix: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
