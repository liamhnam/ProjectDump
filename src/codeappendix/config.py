"""Settings: built-in presets, the ``codeappendix.toml`` file, and validation.

Precedence (lowest to highest): preset -> config file -> command-line flags.
"""

from __future__ import annotations

import difflib
import sys
from dataclasses import dataclass, field, fields, replace
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover - exercised on Python < 3.11 only
    import tomli as tomllib

CONFIG_FILENAME = "codeappendix.toml"


class ConfigError(Exception):
    """A setting is invalid; the message is ready to show to the user."""


@dataclass
class Config:
    # [document]
    language: str = "vi"
    title: str = ""  # empty -> derived from ``label`` and ``language``
    label: str = "A"
    project_name: str = ""  # empty -> the project folder name
    tree: str = "included"
    summary_table: bool = True
    file_info: bool = True
    file_heading: str = "heading"
    page_break_per_file: bool = False
    page_numbers: bool = True
    # [page]
    page_size: str = "A4"
    margin_top: float = 2.0
    margin_bottom: float = 2.0
    margin_left: float = 3.0
    margin_right: float = 2.0
    # [text]
    font: str = "Times New Roman"
    font_size: float = 13
    line_spacing: float = 1.3
    # [code]
    code_font: str = "Consolas"
    code_size: float = 10
    line_numbers: bool = True
    highlight: str = "color"
    theme: str = "vs"
    tab_size: int = 4
    max_lines: int = 0
    # [files]
    include: List[str] = field(default_factory=list)
    exclude: List[str] = field(default_factory=list)
    only: List[str] = field(default_factory=list)
    order: List[str] = field(default_factory=list)
    use_gitignore: bool = True
    default_excludes: bool = True
    skip_generated: bool = True
    skip_minified: bool = True
    max_file_kb: int = 1024

    @property
    def effective_title(self) -> str:
        if self.title:
            return self.title
        if self.language == "en":
            prefix = f"APPENDIX {self.label}. " if self.label else ""
            return prefix + "SOURCE CODE"
        prefix = f"PHỤ LỤC {self.label}. " if self.label else ""
        return prefix + "MÃ NGUỒN CHƯƠNG TRÌNH"


# TOML layout: section -> keys. Each key is also the Config attribute name.
SECTIONS: Dict[str, Tuple[str, ...]] = {
    "document": (
        "language", "title", "label", "project_name", "tree", "summary_table",
        "file_info", "file_heading", "page_break_per_file", "page_numbers",
    ),
    "page": ("page_size", "margin_top", "margin_bottom", "margin_left", "margin_right"),
    "text": ("font", "font_size", "line_spacing"),
    "code": (
        "code_font", "code_size", "line_numbers", "highlight", "theme",
        "tab_size", "max_lines",
    ),
    "files": (
        "include", "exclude", "only", "order", "use_gitignore",
        "default_excludes", "skip_generated", "skip_minified", "max_file_kb",
    ),
}

CHOICES: Dict[str, Tuple[str, ...]] = {
    "language": ("vi", "en"),
    "tree": ("included", "all", "none"),
    "file_heading": ("heading", "plain"),
    "page_size": ("A4", "A5", "Letter"),
    "highlight": ("color", "mono", "none"),
}

PRESETS: Dict[str, Dict[str, Any]] = {
    # Common Vietnamese thesis layout: A4, Times New Roman 13, left margin 3 cm.
    "vn-thesis": {},
    # Fewer pages: smaller code, narrower margins, no per-file info line.
    "compact": {
        "margin_top": 1.5,
        "margin_bottom": 1.5,
        "margin_left": 2.5,
        "margin_right": 1.5,
        "font_size": 12,
        "line_spacing": 1.15,
        "code_size": 8.5,
        "file_info": False,
    },
    # English labels on US Letter with one-inch margins.
    "us-letter": {
        "language": "en",
        "page_size": "Letter",
        "margin_top": 2.54,
        "margin_bottom": 2.54,
        "margin_left": 2.54,
        "margin_right": 2.54,
        "font_size": 12,
        "line_spacing": 1.15,
    },
}
DEFAULT_PRESET = "vn-thesis"

_FIELD_TYPES = {f.name: f.type for f in fields(Config)}


def _suggest(name: str, candidates) -> str:
    match = difflib.get_close_matches(name, list(candidates), n=1)
    return f" (did you mean '{match[0]}'?)" if match else ""


def _coerce(key: str, value: Any) -> Any:
    """Check ``value`` against the declared type of ``key`` and normalise it."""
    kind = _FIELD_TYPES[key]
    if kind == "bool":
        if not isinstance(value, bool):
            raise ConfigError(f"'{key}' must be true or false, got {value!r}")
        return value
    if kind == "int":
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ConfigError(f"'{key}' must be a whole number >= 0, got {value!r}")
        return value
    if kind == "float":
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
            raise ConfigError(f"'{key}' must be a positive number, got {value!r}")
        return float(value)
    if kind == "List[str]":
        if isinstance(value, str):
            value = [value]
        if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
            raise ConfigError(f"'{key}' must be a list of glob patterns, got {value!r}")
        return [v.strip() for v in value if v.strip()]
    if not isinstance(value, str):
        raise ConfigError(f"'{key}' must be text, got {value!r}")
    if key in CHOICES:
        for choice in CHOICES[key]:
            if value.lower() == choice.lower():
                return choice
        raise ConfigError(
            f"'{key}' must be one of {', '.join(CHOICES[key])}, got {value!r}"
        )
    return value


def apply(cfg: Config, values: Dict[str, Any]) -> Config:
    """Return a copy of ``cfg`` with flat ``values`` applied and validated."""
    clean = {}
    for key, value in values.items():
        if key not in _FIELD_TYPES:
            raise ConfigError(f"Unknown setting '{key}'{_suggest(key, _FIELD_TYPES)}")
        clean[key] = _coerce(key, value)
    return replace(cfg, **clean)


def preset(name: str) -> Config:
    if name not in PRESETS:
        raise ConfigError(
            f"Unknown preset '{name}'{_suggest(name, PRESETS)}. "
            f"Available: {', '.join(PRESETS)}"
        )
    return apply(Config(), PRESETS[name])


def flatten_toml(data: Dict[str, Any], source: str) -> Tuple[Optional[str], Dict[str, Any]]:
    """Turn the sectioned TOML table into ``(preset name, flat settings)``."""
    preset_name = data.pop("preset", None)
    if preset_name is not None and not isinstance(preset_name, str):
        raise ConfigError(f"{source}: 'preset' must be text")
    flat: Dict[str, Any] = {}
    for section, table in data.items():
        if section not in SECTIONS:
            raise ConfigError(
                f"{source}: unknown section [{section}]{_suggest(section, SECTIONS)}"
            )
        if not isinstance(table, dict):
            raise ConfigError(f"{source}: [{section}] must be a table")
        for key, value in table.items():
            if key not in SECTIONS[section]:
                raise ConfigError(
                    f"{source}: unknown key '{key}' in [{section}]"
                    f"{_suggest(key, SECTIONS[section])}"
                )
            flat[key] = value
    return preset_name, flat


def load_file(path: Path) -> Tuple[Optional[str], Dict[str, Any]]:
    try:
        with open(path, "rb") as fh:
            data = tomllib.load(fh)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"{path}: invalid TOML: {exc}") from None
    return flatten_toml(data, str(path))


def resolve(
    project: Path,
    config_path: Optional[Path] = None,
    preset_name: Optional[str] = None,
    overrides: Optional[Dict[str, Any]] = None,
) -> Tuple[Config, Optional[Path]]:
    """Build the final Config. Returns it with the config file used (if any)."""
    if config_path is None:
        candidate = project / CONFIG_FILENAME
        config_path = candidate if candidate.is_file() else None
    elif not config_path.is_file():
        raise ConfigError(f"Config file not found: {config_path}")

    file_preset, file_values = (None, {})
    if config_path is not None:
        file_preset, file_values = load_file(config_path)

    cfg = preset(preset_name or file_preset or DEFAULT_PRESET)
    cfg = apply(cfg, file_values)
    cfg = apply(cfg, overrides or {})
    _check_theme(cfg.theme)
    return cfg, config_path


def _check_theme(theme: str) -> None:
    from pygments.styles import get_all_styles

    styles = sorted(get_all_styles())
    if theme not in styles:
        raise ConfigError(f"Unknown theme '{theme}'{_suggest(theme, styles)}")


def render_template(preset_name: str = DEFAULT_PRESET) -> str:
    """The commented ``codeappendix.toml`` written by ``codeappendix init``."""
    c = preset(preset_name)

    def b(v: bool) -> str:
        return "true" if v else "false"

    def num(v: float) -> str:
        return f"{v:g}"

    return f'''# Cấu hình CodeAppendix — https://github.com/liamhnam/CodeAppendix
# Mọi dòng đều không bắt buộc; xoá dòng nào thì dùng giá trị mặc định của preset.
preset = "{preset_name}"   # vn-thesis | compact | us-letter

[document]
language = "{c.language}"            # vi | en — ngôn ngữ của nhãn trong tài liệu
label = "{c.label}"                  # "A" -> "PHỤ LỤC A", các tệp đánh số A.1, A.2, ...
# title = "PHỤ LỤC A. MÃ NGUỒN CHƯƠNG TRÌNH"   # tự đặt tiêu đề
# project_name = "Hệ thống quản lý thư viện"   # mặc định: tên thư mục
tree = "{c.tree}"             # included | all | none — cây thư mục
summary_table = {b(c.summary_table)}         # bảng thống kê tệp, có cột số trang
file_info = {b(c.file_info)}             # dòng "Ngôn ngữ · số dòng" dưới tên tệp
file_heading = "{c.file_heading}"       # heading: hiện trong mục lục Word | plain: không hiện
page_break_per_file = {b(c.page_break_per_file)}  # mỗi tệp bắt đầu trang mới
page_numbers = {b(c.page_numbers)}          # số trang ở chân trang

[page]
page_size = "{c.page_size}"            # A4 | A5 | Letter
margin_top = {num(c.margin_top)}             # cm
margin_bottom = {num(c.margin_bottom)}
margin_left = {num(c.margin_left)}
margin_right = {num(c.margin_right)}

[text]
font = "{c.font}"
font_size = {num(c.font_size)}
line_spacing = {num(c.line_spacing)}

[code]
code_font = "{c.code_font}"
code_size = {num(c.code_size)}
line_numbers = {b(c.line_numbers)}
highlight = "{c.highlight}"          # color | mono (in đen trắng) | none
theme = "{c.theme}"                 # bảng màu Pygments: vs, default, friendly, xcode, ...
tab_size = {c.tab_size}
max_lines = {c.max_lines}               # >0: tệp dài hơn chỉ giữ phần đầu và cuối

[files]
include = []   # thêm tệp ngoài mã nguồn, ví dụ ["*.json", "app/src/main/res/layout/*.xml"]
exclude = []   # bỏ bớt, ví dụ ["tests/**", "**/migrations/**"]
only = []      # nếu có: chỉ lấy các tệp khớp, ví dụ ["src/**"]
order = []     # đưa các tệp này lên đầu theo thứ tự, ví dụ ["src/main.py", "src/app/**"]
use_gitignore = {b(c.use_gitignore)}
default_excludes = {b(c.default_excludes)}   # bỏ node_modules, venv, build, dist, ...
skip_generated = {b(c.skip_generated)}     # bỏ tệp do công cụ sinh ra ("DO NOT EDIT", *.g.dart, ...)
skip_minified = {b(c.skip_minified)}      # bỏ tệp đã nén (*.min.js, ...)
max_file_kb = {c.max_file_kb}        # bỏ tệp lớn hơn mức này
'''
