"""Page geometry shared by the document writer and the page-count estimate."""

from __future__ import annotations

import math
from typing import List

from .config import Config

CM_TO_PT = 72 / 2.54

PAGE_SIZES_CM = {
    "A4": (21.0, 29.7),
    "A5": (14.8, 21.0),
    "Letter": (21.59, 27.94),
}


def char_width_em(font: str) -> float:
    """Advance width of one character of a monospaced font, in em."""
    name = font.lower()
    if "consolas" in name:
        return 0.55
    if "courier" in name or "liberation mono" in name:
        return 0.6
    return 0.6  # safe upper bound for other monospaced fonts


def number_width(max_line: int) -> int:
    return len(str(max_line))


def code_indent_pt(cfg: Config, digits: int) -> float:
    """Where code starts when line numbers are shown (hanging indent)."""
    if not cfg.line_numbers:
        return 0.0
    return (digits + 2) * cfg.code_size * char_width_em(cfg.code_font)


def usable_width_pt(cfg: Config) -> float:
    width, _ = PAGE_SIZES_CM[cfg.page_size]
    return (width - cfg.margin_left - cfg.margin_right) * CM_TO_PT


def usable_height_pt(cfg: Config) -> float:
    _, height = PAGE_SIZES_CM[cfg.page_size]
    return (height - cfg.margin_top - cfg.margin_bottom) * CM_TO_PT


def code_line_height_pt(cfg: Config) -> float:
    return cfg.code_size * 1.17


def text_line_height_pt(cfg: Config, size: float) -> float:
    return size * 1.15 * cfg.line_spacing


def wrapped_rows(lines: List[str], cfg: Config, digits: int) -> int:
    """How many printed rows ``lines`` take once long lines wrap."""
    avail = usable_width_pt(cfg) - code_indent_pt(cfg, digits)
    per_row = max(20, int(avail / (cfg.code_size * char_width_em(cfg.code_font))))
    return sum(max(1, math.ceil(len(line) / per_row)) for line in lines)
